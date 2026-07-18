import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import process from "node:process";
import { fileURLToPath, URL } from "node:url";

import ts from "typescript";

const repositoryRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const ignoredParts = new Set([".venv", "dist", "generated", "node_modules"]);
const scanRoots = ["apps", "packages", "tooling"].map((part) => resolve(repositoryRoot, part));

function discoverSourceFiles(root) {
  if (!existsSync(root)) return [];
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (ignoredParts.has(entry.name)) continue;
    const path = resolve(root, entry.name);
    if (entry.isDirectory()) files.push(...discoverSourceFiles(path));
    else if (/\.(?:[cm]?[jt]s|[jt]sx)$/u.test(entry.name)) files.push(path);
  }
  return files;
}

function parseArguments(arguments_) {
  let safetyRoot = resolve(repositoryRoot, "packages", "safety");
  const files = [];
  for (let index = 0; index < arguments_.length; index += 1) {
    if (arguments_[index] === "--safety-root") {
      index += 1;
      if (index >= arguments_.length) throw new Error("--safety-root requires a path");
      safetyRoot = resolve(arguments_[index]);
    } else {
      files.push(resolve(arguments_[index]));
    }
  }
  return {
    files: files.length > 0 ? files : scanRoots.flatMap(discoverSourceFiles).sort(),
    safetyRoot,
  };
}

function loadCompilerOptions() {
  const configPath = resolve(repositoryRoot, "tsconfig.base.json");
  const loaded = ts.readConfigFile(configPath, ts.sys.readFile);
  if (loaded.error !== undefined) {
    throw new Error(ts.flattenDiagnosticMessageText(loaded.error.messageText, " "));
  }
  const parsed = ts.parseJsonConfigFileContent(
    loaded.config,
    ts.sys,
    repositoryRoot,
    {
      noEmit: true,
      skipLibCheck: false,
      types: ["node"],
    },
    configPath,
  );
  if (parsed.errors.length > 0) {
    throw new Error(
      parsed.errors
        .map((diagnostic) => ts.flattenDiagnosticMessageText(diagnostic.messageText, " "))
        .join("; "),
    );
  }
  return parsed.options;
}

function isUnder(path, root) {
  const relation = relative(root, path);
  return relation === "" || (!relation.startsWith(`..${sep}`) && relation !== "..");
}

function resolveAliasSymbol(symbol, checker) {
  const seen = new Set();
  let current = symbol;
  while (
    current !== undefined &&
    (current.flags & ts.SymbolFlags.Alias) !== 0 &&
    !seen.has(current)
  ) {
    seen.add(current);
    current = checker.getAliasedSymbol(current);
  }
  return current;
}

function symbolIsApprovedResponse(symbol, checker) {
  if (symbol === undefined) return false;
  const seen = new Set();
  let current = symbol;
  while (current !== undefined && !seen.has(current)) {
    seen.add(current);
    if (current.getName() === "ApprovedResponse") return true;
    if ((current.flags & ts.SymbolFlags.Alias) === 0) return false;
    current = resolveAliasSymbol(current, checker);
  }
  return false;
}

function typeNodeReferencesApprovedResponse(node, checker) {
  let found = false;
  function visit(candidate) {
    if (found) return;
    if (ts.isTypeReferenceNode(candidate)) {
      found = symbolIsApprovedResponse(checker.getSymbolAtLocation(candidate.typeName), checker);
    } else if (ts.isExpressionWithTypeArguments(candidate)) {
      found = symbolIsApprovedResponse(checker.getSymbolAtLocation(candidate.expression), checker);
    }
    if (!found) ts.forEachChild(candidate, visit);
  }
  visit(node);
  return found;
}

function typeNodeIsApprovedResponseAlias(node, checker, seen = new Set()) {
  if (ts.isParenthesizedTypeNode(node) || ts.isTypeOperatorNode(node)) {
    return typeNodeIsApprovedResponseAlias(node.type, checker, seen);
  }
  if (ts.isUnionTypeNode(node) || ts.isIntersectionTypeNode(node)) {
    return node.types.some((member) => typeNodeIsApprovedResponseAlias(member, checker, seen));
  }
  if (!ts.isTypeReferenceNode(node)) return false;
  const symbol = checker.getSymbolAtLocation(node.typeName);
  if (symbolIsApprovedResponse(symbol, checker)) return true;
  const resolved = resolveAliasSymbol(symbol, checker);
  if (resolved === undefined || seen.has(resolved)) return false;
  seen.add(resolved);
  return (resolved.declarations ?? []).some(
    (declaration) =>
      ts.isTypeAliasDeclaration(declaration) &&
      typeNodeIsApprovedResponseAlias(declaration.type, checker, seen),
  );
}

function typeIsApprovedResponse(type, checker, seen = new Set()) {
  if (type === undefined || seen.has(type)) return false;
  seen.add(type);
  if (
    symbolIsApprovedResponse(type.aliasSymbol, checker) ||
    symbolIsApprovedResponse(type.getSymbol(), checker)
  ) {
    return true;
  }
  if (
    type.isUnionOrIntersection() &&
    type.types.some((member) => typeIsApprovedResponse(member, checker, seen))
  ) {
    return true;
  }
  for (const declaration of type.aliasSymbol?.declarations ?? []) {
    if (
      ts.isTypeAliasDeclaration(declaration) &&
      typeNodeIsApprovedResponseAlias(declaration.type, checker)
    ) {
      return true;
    }
  }
  return (type.getBaseTypes?.() ?? []).some((base) => typeIsApprovedResponse(base, checker, seen));
}

function typeContainsApprovedResponse(type, checker, seen = new Set()) {
  if (type === undefined || seen.has(type)) return false;
  seen.add(type);
  if (typeIsApprovedResponse(type, checker)) return true;
  if (type.isUnionOrIntersection()) {
    return type.types.some((member) => typeContainsApprovedResponse(member, checker, seen));
  }
  if ((type.flags & ts.TypeFlags.Object) === 0) return false;
  for (const argument of type.aliasTypeArguments ?? []) {
    if (typeContainsApprovedResponse(argument, checker, seen)) return true;
  }
  if ((type.objectFlags & ts.ObjectFlags.Reference) !== 0) {
    for (const argument of checker.getTypeArguments(type)) {
      if (typeContainsApprovedResponse(argument, checker, seen)) return true;
    }
  }
  const symbol = type.getSymbol();
  const inspectProperties =
    symbol === undefined ||
    (symbol.declarations ?? []).some(
      (declaration) =>
        !declaration.getSourceFile().isDeclarationFile ||
        ts.isTypeLiteralNode(declaration) ||
        ts.isObjectLiteralExpression(declaration),
    );
  if (!inspectProperties) return false;
  for (const property of checker.getPropertiesOfType(type)) {
    const declaration = property.valueDeclaration ?? property.declarations?.[0];
    if (
      declaration !== undefined &&
      typeContainsApprovedResponse(
        checker.getTypeOfSymbolAtLocation(property, declaration),
        checker,
        seen,
      )
    ) {
      return true;
    }
  }
  return false;
}

function typeRequiresApprovedResponse(type, checker) {
  if (type === undefined) return false;
  if (!type.isUnion()) return typeIsApprovedResponse(type, checker);
  const nonNullish = type.types.filter(
    (member) => (member.flags & (ts.TypeFlags.Null | ts.TypeFlags.Undefined)) === 0,
  );
  return (
    nonNullish.length > 0 && nonNullish.every((member) => typeIsApprovedResponse(member, checker))
  );
}

function callDeclarationIsSafetyOwned(node, checker, safetyRoot) {
  const declaration = checker.getResolvedSignature(node)?.declaration;
  return declaration !== undefined && isUnder(declaration.getSourceFile().fileName, safetyRoot);
}

function containingVariableDeclaration(node) {
  let current = node.parent;
  while (current !== undefined && !ts.isVariableDeclaration(current)) current = current.parent;
  return current;
}

function symbolHasTrustedApprovedResponseOrigin(
  symbol,
  checker,
  safetyRoot,
  container,
  seenSymbols,
) {
  const resolved = resolveAliasSymbol(symbol, checker);
  if (resolved === undefined || seenSymbols.has(resolved)) return false;
  seenSymbols.add(resolved);
  const declarations = resolved.declarations ?? [];
  if (
    declarations.some((declaration) => isUnder(declaration.getSourceFile().fileName, safetyRoot))
  ) {
    return true;
  }
  if (declarations.some(ts.isParameter)) return true;
  for (const declaration of declarations) {
    let initializer;
    if (ts.isVariableDeclaration(declaration) || ts.isPropertyDeclaration(declaration)) {
      initializer = declaration.initializer;
    } else if (ts.isBindingElement(declaration)) {
      initializer = containingVariableDeclaration(declaration)?.initializer;
    }
    if (
      initializer !== undefined &&
      (container
        ? expressionHasTrustedApprovedResponseContainerOrigin(
            initializer,
            checker,
            safetyRoot,
            seenSymbols,
          )
        : expressionHasTrustedApprovedResponseOrigin(initializer, checker, safetyRoot, seenSymbols))
    ) {
      return true;
    }
  }
  return false;
}

function expressionHasTrustedApprovedResponseOrigin(
  expression,
  checker,
  safetyRoot,
  seenSymbols = new Set(),
) {
  if (ts.isParenthesizedExpression(expression) || ts.isNonNullExpression(expression)) {
    return expressionHasTrustedApprovedResponseOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  if (ts.isAwaitExpression(expression)) {
    return expressionHasTrustedApprovedResponseContainerOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  if (ts.isCallExpression(expression) || ts.isNewExpression(expression)) {
    return callDeclarationIsSafetyOwned(expression, checker, safetyRoot);
  }
  if (ts.isConditionalExpression(expression)) {
    return (
      expressionHasTrustedApprovedResponseOrigin(
        expression.whenTrue,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      ) &&
      expressionHasTrustedApprovedResponseOrigin(
        expression.whenFalse,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      )
    );
  }
  const symbol = checker.getSymbolAtLocation(expression);
  if (symbolHasTrustedApprovedResponseOrigin(symbol, checker, safetyRoot, false, seenSymbols)) {
    return true;
  }
  if (ts.isPropertyAccessExpression(expression) || ts.isElementAccessExpression(expression)) {
    return expressionHasTrustedApprovedResponseContainerOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  return false;
}

function expressionHasTrustedApprovedResponseContainerOrigin(
  expression,
  checker,
  safetyRoot,
  seenSymbols = new Set(),
) {
  if (ts.isParenthesizedExpression(expression) || ts.isNonNullExpression(expression)) {
    return expressionHasTrustedApprovedResponseContainerOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  if (ts.isAwaitExpression(expression)) {
    return expressionHasTrustedApprovedResponseContainerOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  if (ts.isCallExpression(expression) || ts.isNewExpression(expression)) {
    return callDeclarationIsSafetyOwned(expression, checker, safetyRoot);
  }
  if (ts.isConditionalExpression(expression)) {
    return (
      expressionHasTrustedApprovedResponseContainerOrigin(
        expression.whenTrue,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      ) &&
      expressionHasTrustedApprovedResponseContainerOrigin(
        expression.whenFalse,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      )
    );
  }
  const symbol = checker.getSymbolAtLocation(expression);
  if (symbolHasTrustedApprovedResponseOrigin(symbol, checker, safetyRoot, true, seenSymbols)) {
    return true;
  }
  if (ts.isArrayLiteralExpression(expression)) {
    return expression.elements.every((element) => {
      const value = ts.isSpreadElement(element) ? element.expression : element;
      const valueType = checker.getTypeAtLocation(value);
      const contextualType = checker.getContextualType(value);
      if (
        !typeContainsApprovedResponse(valueType, checker) &&
        !typeContainsApprovedResponse(contextualType, checker)
      ) {
        return true;
      }
      return typeRequiresApprovedResponse(contextualType, checker) ||
        typeIsApprovedResponse(valueType, checker)
        ? expressionHasTrustedApprovedResponseOrigin(
            value,
            checker,
            safetyRoot,
            new Set(seenSymbols),
          )
        : expressionHasTrustedApprovedResponseContainerOrigin(
            value,
            checker,
            safetyRoot,
            new Set(seenSymbols),
          );
    });
  }
  if (ts.isObjectLiteralExpression(expression)) {
    return expression.properties.every((property) => {
      let value;
      if (ts.isPropertyAssignment(property)) value = property.initializer;
      else if (ts.isShorthandPropertyAssignment(property)) value = property.name;
      else if (ts.isSpreadAssignment(property)) value = property.expression;
      else return true;
      const valueType = checker.getTypeAtLocation(value);
      const contextualType = checker.getContextualType(value);
      if (
        !typeContainsApprovedResponse(valueType, checker) &&
        !typeContainsApprovedResponse(contextualType, checker)
      ) {
        return true;
      }
      return typeRequiresApprovedResponse(contextualType, checker) ||
        typeIsApprovedResponse(valueType, checker)
        ? expressionHasTrustedApprovedResponseOrigin(
            value,
            checker,
            safetyRoot,
            new Set(seenSymbols),
          )
        : expressionHasTrustedApprovedResponseContainerOrigin(
            value,
            checker,
            safetyRoot,
            new Set(seenSymbols),
          );
    });
  }
  if (ts.isPropertyAccessExpression(expression) || ts.isElementAccessExpression(expression)) {
    return expressionHasTrustedApprovedResponseContainerOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  return false;
}

function sourceHasApprovedResponseProvenance(expression, targetType, checker, safetyRoot) {
  const type = checker.getTypeAtLocation(expression);
  if ((type.flags & ts.TypeFlags.Never) !== 0) return false;
  if ((type.flags & (ts.TypeFlags.Null | ts.TypeFlags.Undefined)) !== 0) {
    return checker.isTypeAssignableTo(type, targetType);
  }
  return (
    typeIsApprovedResponse(type, checker) &&
    expressionHasTrustedApprovedResponseOrigin(expression, checker, safetyRoot)
  );
}

function sourceHasApprovedResponseContainerProvenance(expression, targetType, checker, safetyRoot) {
  const type = checker.getTypeAtLocation(expression);
  if ((type.flags & ts.TypeFlags.Never) !== 0) return false;
  if ((type.flags & (ts.TypeFlags.Null | ts.TypeFlags.Undefined)) !== 0) {
    return checker.isTypeAssignableTo(type, targetType);
  }
  return (
    typeContainsApprovedResponse(type, checker) &&
    expressionHasTrustedApprovedResponseContainerOrigin(expression, checker, safetyRoot)
  );
}

function isApprovedResponseDeclaration(node) {
  return (
    (ts.isInterfaceDeclaration(node) ||
      ts.isTypeAliasDeclaration(node) ||
      ts.isClassDeclaration(node)) &&
    node.name !== undefined &&
    node.name.text === "ApprovedResponse"
  );
}

function isPrivateSafetyModuleSpecifier(specifier, sourceFile, safetyRoot) {
  const normalized = specifier.replaceAll("\\", "/");
  const normalizedLower = normalized.toLowerCase();
  let segments;
  let target;
  if (normalizedLower.startsWith("file:")) {
    try {
      target = fileURLToPath(new URL(specifier));
    } catch {
      return false;
    }
  } else if (normalized.startsWith(".")) {
    target = resolve(dirname(sourceFile.fileName), normalized);
  } else if (isAbsolute(normalized)) {
    target = resolve(normalized);
  }
  if (target !== undefined) {
    if (!isUnder(target, safetyRoot)) return false;
    segments = relative(safetyRoot, target).split(sep);
  } else if (normalizedLower.startsWith("@vnova/safety/")) {
    segments = normalized.slice("@vnova/safety/".length).split("/");
  } else {
    return false;
  }
  return segments.some(isPrivateSafetyPathSegment);
}

function isPrivateSafetyPathSegment(segment) {
  const stem = segment.toLowerCase().replace(/\.(?:[cm]?[jt]s|[jt]sx|d\.ts)$/u, "");
  return stem === "_mint" || stem === "internal" || stem === "private";
}

function isPrivateSafetySourceFile(file, safetyRoot) {
  return (
    isUnder(file, safetyRoot) &&
    relative(safetyRoot, file).split(sep).some(isPrivateSafetyPathSegment)
  );
}

function moduleSpecifierText(node, stringConstants = new Map()) {
  if (
    (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) &&
    node.moduleSpecifier !== undefined &&
    ts.isStringLiteralLike(node.moduleSpecifier)
  ) {
    return node.moduleSpecifier.text;
  }
  if (
    ts.isImportTypeNode(node) &&
    ts.isLiteralTypeNode(node.argument) &&
    ts.isStringLiteralLike(node.argument.literal)
  ) {
    return node.argument.literal.text;
  }
  if (
    ts.isImportEqualsDeclaration(node) &&
    ts.isExternalModuleReference(node.moduleReference) &&
    node.moduleReference.expression !== undefined &&
    ts.isStringLiteralLike(node.moduleReference.expression)
  ) {
    return node.moduleReference.expression.text;
  }
  if (ts.isCallExpression(node) && node.arguments.length >= 1) {
    const argument = node.arguments[0];
    const specifier = ts.isStringLiteralLike(argument)
      ? argument.text
      : ts.isIdentifier(argument)
        ? stringConstants.get(argument.text)
        : undefined;
    if (
      specifier !== undefined &&
      (node.expression.kind === ts.SyntaxKind.ImportKeyword ||
        (ts.isIdentifier(node.expression) && node.expression.text === "require") ||
        (ts.isPropertyAccessExpression(node.expression) &&
          ts.isIdentifier(node.expression.expression) &&
          node.expression.expression.text === "module" &&
          node.expression.name.text === "require"))
    ) {
      return specifier;
    }
  }
  return undefined;
}

function isDynamicModuleLoaderSurface(node) {
  if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
    return true;
  }
  if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) {
    return true;
  }
  if (ts.isIdentifier(node)) {
    return node.text === "require" || node.text === "createRequire";
  }
  if (ts.isPropertyAccessExpression(node)) {
    return node.name.text === "require" || node.name.text === "createRequire";
  }
  if (ts.isElementAccessExpression(node)) {
    const member = node.argumentExpression;
    return (
      member !== undefined &&
      ts.isStringLiteralLike(member) &&
      (member.text === "require" || member.text === "createRequire")
    );
  }
  return false;
}

function bodyReturnsPrivateSafetyCapability(body, checker, safetyRoot, seenSymbols) {
  let leaked = false;
  function visit(node) {
    if (
      !leaked &&
      ts.isReturnStatement(node) &&
      node.expression !== undefined &&
      expressionHasPrivateSafetyCapabilityOrigin(
        node.expression,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      )
    ) {
      leaked = true;
      return;
    }
    if (!leaked) ts.forEachChild(node, visit);
  }
  visit(body);
  return leaked;
}

function expressionHasPrivateSafetyCapabilityOrigin(
  expression,
  checker,
  safetyRoot,
  seenSymbols = new Set(),
) {
  if (
    ts.isParenthesizedExpression(expression) ||
    ts.isNonNullExpression(expression) ||
    ts.isAsExpression(expression) ||
    ts.isTypeAssertionExpression(expression) ||
    ts.isSatisfiesExpression(expression)
  ) {
    return expressionHasPrivateSafetyCapabilityOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  if (ts.isConditionalExpression(expression)) {
    return (
      expressionHasPrivateSafetyCapabilityOrigin(
        expression.whenTrue,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      ) ||
      expressionHasPrivateSafetyCapabilityOrigin(
        expression.whenFalse,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      )
    );
  }
  if (ts.isArrayLiteralExpression(expression)) {
    return expression.elements.some((element) =>
      expressionHasPrivateSafetyCapabilityOrigin(
        ts.isSpreadElement(element) ? element.expression : element,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      ),
    );
  }
  if (ts.isObjectLiteralExpression(expression)) {
    return expression.properties.some((property) => {
      let value;
      if (ts.isPropertyAssignment(property)) value = property.initializer;
      else if (ts.isShorthandPropertyAssignment(property)) value = property.name;
      else if (ts.isSpreadAssignment(property)) value = property.expression;
      else if (
        (ts.isMethodDeclaration(property) ||
          ts.isGetAccessorDeclaration(property) ||
          ts.isSetAccessorDeclaration(property)) &&
        property.body !== undefined
      ) {
        return bodyReturnsPrivateSafetyCapability(
          property.body,
          checker,
          safetyRoot,
          new Set(seenSymbols),
        );
      }
      return (
        value !== undefined &&
        expressionHasPrivateSafetyCapabilityOrigin(value, checker, safetyRoot, new Set(seenSymbols))
      );
    });
  }
  if (ts.isArrowFunction(expression) && !ts.isBlock(expression.body)) {
    return expressionHasPrivateSafetyCapabilityOrigin(
      expression.body,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  if (ts.isFunctionExpression(expression) || ts.isArrowFunction(expression)) {
    return bodyReturnsPrivateSafetyCapability(expression.body, checker, safetyRoot, seenSymbols);
  }
  if (ts.isCallExpression(expression) || ts.isNewExpression(expression)) {
    if (
      ts.isPropertyAccessExpression(expression.expression) &&
      expression.expression.name.text === "bind" &&
      expressionHasPrivateSafetyCapabilityOrigin(
        expression.expression.expression,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      )
    ) {
      return true;
    }
    if (
      expressionHasPrivateSafetyCapabilityOrigin(
        expression.expression,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      )
    ) {
      return false;
    }
    return (expression.arguments ?? []).some((argument) =>
      expressionHasPrivateSafetyCapabilityOrigin(
        argument,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      ),
    );
  }
  const symbol = checker.getSymbolAtLocation(expression);
  if (symbolHasPrivateSafetyCapabilityOrigin(symbol, checker, safetyRoot, seenSymbols)) {
    return true;
  }
  if (ts.isPropertyAccessExpression(expression) || ts.isElementAccessExpression(expression)) {
    return expressionHasPrivateSafetyCapabilityOrigin(
      expression.expression,
      checker,
      safetyRoot,
      seenSymbols,
    );
  }
  return false;
}

function symbolHasPrivateSafetyCapabilityOrigin(symbol, checker, safetyRoot, seenSymbols) {
  if (symbol === undefined || seenSymbols.has(symbol)) return false;
  seenSymbols.add(symbol);
  const resolved = resolveAliasSymbol(symbol, checker) ?? symbol;
  if (resolved !== symbol && seenSymbols.has(resolved)) return false;
  seenSymbols.add(resolved);
  const declarations = resolved.declarations ?? symbol.declarations ?? [];
  if (
    declarations.some((declaration) =>
      isPrivateSafetySourceFile(declaration.getSourceFile().fileName, safetyRoot),
    )
  ) {
    return true;
  }
  return declarations.some((declaration) => {
    if (
      (ts.isVariableDeclaration(declaration) || ts.isPropertyDeclaration(declaration)) &&
      declaration.initializer !== undefined
    ) {
      return expressionHasPrivateSafetyCapabilityOrigin(
        declaration.initializer,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      );
    }
    if (ts.isExportAssignment(declaration)) {
      return expressionHasPrivateSafetyCapabilityOrigin(
        declaration.expression,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      );
    }
    if (ts.isFunctionDeclaration(declaration) && declaration.body !== undefined) {
      return bodyReturnsPrivateSafetyCapability(
        declaration.body,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      );
    }
    if (ts.isClassDeclaration(declaration)) {
      return bodyReturnsPrivateSafetyCapability(
        declaration,
        checker,
        safetyRoot,
        new Set(seenSymbols),
      );
    }
    return false;
  });
}

function symbolIsExportedFromSource(symbol, sourceFile, checker) {
  const moduleSymbol = checker.getSymbolAtLocation(sourceFile);
  if (moduleSymbol === undefined) return false;
  return checker
    .getExportsOfModule(moduleSymbol)
    .some((candidate) => resolveAliasSymbol(candidate, checker) === symbol);
}

function isTrueLiteralType(node) {
  return (
    node !== undefined &&
    ts.isLiteralTypeNode(node) &&
    node.literal.kind === ts.SyntaxKind.TrueKeyword
  );
}

function isPrivateUniqueSymbolBrand(member, sourceFile, checker) {
  if (
    !ts.isPropertySignature(member) ||
    !ts.isComputedPropertyName(member.name) ||
    !member.modifiers?.some((modifier) => modifier.kind === ts.SyntaxKind.ReadonlyKeyword) ||
    !isTrueLiteralType(member.type)
  ) {
    return false;
  }
  const brandSymbol = resolveAliasSymbol(
    checker.getSymbolAtLocation(member.name.expression),
    checker,
  );
  if (brandSymbol === undefined || symbolIsExportedFromSource(brandSymbol, sourceFile, checker)) {
    return false;
  }
  const declaration = brandSymbol.declarations?.find(
    (candidate) => ts.isVariableDeclaration(candidate) && candidate.getSourceFile() === sourceFile,
  );
  if (declaration === undefined || !ts.isVariableDeclaration(declaration)) return false;
  const declarationList = declaration.parent;
  const statement = declarationList.parent;
  if (
    !ts.isVariableDeclarationList(declarationList) ||
    (declarationList.flags & ts.NodeFlags.Const) === 0 ||
    !ts.isVariableStatement(statement) ||
    statement.parent !== sourceFile
  ) {
    return false;
  }
  const brandType = checker.getTypeOfSymbolAtLocation(brandSymbol, declaration.name);
  return (brandType.flags & ts.TypeFlags.UniqueESSymbol) !== 0;
}

function interfaceHasPrivateNominalBrand(node, sourceFile, checker) {
  const symbol = checker.getSymbolAtLocation(node.name);
  const declarations = (symbol?.declarations ?? []).filter(ts.isInterfaceDeclaration);
  return declarations.some((declaration) =>
    declaration.members.some((member) => isPrivateUniqueSymbolBrand(member, sourceFile, checker)),
  );
}

function collectApprovedResponseTypes(sourceFiles, checker, safetyRoot) {
  const types = [];
  const symbols = new Set();
  for (const sourceFile of sourceFiles) {
    if (!isUnder(sourceFile.fileName, safetyRoot)) continue;
    function visit(node) {
      if (isApprovedResponseDeclaration(node)) {
        const symbol = checker.getSymbolAtLocation(node.name);
        if (symbol !== undefined && !symbols.has(symbol)) {
          symbols.add(symbol);
          types.push(checker.getDeclaredTypeOfSymbol(symbol));
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(sourceFile);
  }
  return types;
}

function expressionReferencesAlias(expression, aliases, checker) {
  if (ts.isIdentifier(expression) && aliases.has(expression.text)) return true;
  if (ts.isPropertyAccessExpression(expression) && expression.name.text === "ApprovedResponse") {
    return true;
  }
  return symbolIsApprovedResponse(checker.getSymbolAtLocation(expression), checker);
}

function collectValueAliases(sourceFile, checker) {
  const aliases = new Set(["ApprovedResponse"]);
  function collectImports(node) {
    if (
      ts.isImportSpecifier(node) &&
      (node.propertyName?.text ?? node.name.text) === "ApprovedResponse"
    ) {
      aliases.add(node.name.text);
    }
    ts.forEachChild(node, collectImports);
  }
  collectImports(sourceFile);

  let changed = true;
  while (changed) {
    changed = false;
    function collectDerived(node) {
      if (
        ts.isVariableDeclaration(node) &&
        ts.isIdentifier(node.name) &&
        node.initializer !== undefined &&
        expressionReferencesAlias(node.initializer, aliases, checker) &&
        !aliases.has(node.name.text)
      ) {
        aliases.add(node.name.text);
        changed = true;
      }
      if (
        (ts.isClassDeclaration(node) || ts.isClassExpression(node)) &&
        node.name !== undefined &&
        (node.heritageClauses ?? []).some((clause) =>
          clause.types.some(
            (heritage) =>
              expressionReferencesAlias(heritage.expression, aliases, checker) ||
              typeNodeReferencesApprovedResponse(heritage, checker),
          ),
        ) &&
        !aliases.has(node.name.text)
      ) {
        aliases.add(node.name.text);
        changed = true;
      }
      ts.forEachChild(node, collectDerived);
    }
    collectDerived(sourceFile);
  }
  return aliases;
}

function isForbiddenDefinition(node) {
  const namedDeclaration =
    ts.isClassDeclaration(node) ||
    ts.isInterfaceDeclaration(node) ||
    ts.isTypeAliasDeclaration(node) ||
    ts.isFunctionDeclaration(node) ||
    ts.isEnumDeclaration(node) ||
    ts.isModuleDeclaration(node) ||
    ts.isVariableDeclaration(node);
  return (
    namedDeclaration &&
    node.name !== undefined &&
    ts.isIdentifier(node.name) &&
    node.name.text === "ApprovedResponse"
  );
}

function typePredicateReferencesApprovedResponse(node, checker) {
  return (
    node !== undefined &&
    ts.isTypePredicateNode(node) &&
    node.type !== undefined &&
    typeContainsApprovedResponse(checker.getTypeFromTypeNode(node.type), checker)
  );
}

function collectCompilerDiagnostics(program, rootFiles, safetyRoot) {
  const rootFileSet = new Set(rootFiles.map((file) => resolve(file)));
  return ts
    .getPreEmitDiagnostics(program)
    .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
    .filter(
      (diagnostic) =>
        diagnostic.file === undefined ||
        rootFileSet.has(resolve(diagnostic.file.fileName)) ||
        isUnder(diagnostic.file.fileName, repositoryRoot) ||
        isUnder(diagnostic.file.fileName, safetyRoot),
    )
    .map((diagnostic) => {
      const file = diagnostic.file?.fileName ?? resolve(repositoryRoot, "tsconfig.base.json");
      const location =
        diagnostic.file === undefined || diagnostic.start === undefined
          ? { character: 0, line: 0 }
          : diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
      return {
        column: location.character + 1,
        file,
        line: location.line + 1,
        message:
          "TypeScript program must be error-free for boundary analysis: " +
          ts.flattenDiagnosticMessageText(diagnostic.messageText, " "),
      };
    });
}

function scanSourceFile(sourceFile, checker, safetyRoot, approvedResponseTypes) {
  const aliases = collectValueAliases(sourceFile, checker);
  const violations = [];
  const reported = new Set();

  function report(node, message) {
    const key = `${node.pos}:${node.end}:${message}`;
    if (reported.has(key)) return;
    reported.add(key);
    const location = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
    violations.push({
      column: location.character + 1,
      file: sourceFile.fileName,
      line: location.line + 1,
      message,
    });
  }

  if (isUnder(sourceFile.fileName, safetyRoot)) {
    const privateSafetySource = isPrivateSafetySourceFile(sourceFile.fileName, safetyRoot);
    function visitSafety(node) {
      if (isDynamicModuleLoaderSurface(node)) {
        report(
          node,
          "Dynamic module-loading primitives are forbidden in governed source; " +
            "introduce an ADR-reviewed allowlist before enabling one",
        );
      }
      const specifier = moduleSpecifierText(node);
      if (
        !privateSafetySource &&
        specifier !== undefined &&
        isPrivateSafetyModuleSpecifier(specifier, sourceFile, safetyRoot)
      ) {
        report(node, "A public safety module cannot import or export a private safety module");
      }
      if (isApprovedResponseDeclaration(node)) {
        if (!ts.isInterfaceDeclaration(node)) {
          report(
            node,
            "ApprovedResponse must be a nominal interface with a private unique-symbol brand",
          );
        } else {
          const symbol = checker.getSymbolAtLocation(node.name);
          const declarations = (symbol?.declarations ?? []).filter(ts.isInterfaceDeclaration);
          if (
            declarations[0] === node &&
            !interfaceHasPrivateNominalBrand(node, sourceFile, checker)
          ) {
            report(node, "ApprovedResponse must carry a readonly private unique-symbol brand");
          }
        }
      }
      ts.forEachChild(node, visitSafety);
    }
    visitSafety(sourceFile);
    if (!privateSafetySource) {
      const moduleSymbol = checker.getSymbolAtLocation(sourceFile);
      for (const exported of moduleSymbol === undefined
        ? []
        : checker.getExportsOfModule(moduleSymbol)) {
        if (symbolHasPrivateSafetyCapabilityOrigin(exported, checker, safetyRoot, new Set())) {
          const declaration = (exported.declarations ?? []).find(
            (candidate) => candidate.getSourceFile() === sourceFile,
          );
          report(
            declaration ?? sourceFile,
            "The protected safety mint capability cannot be exported from packages/safety",
          );
        }
      }
    }
    return violations;
  }

  function reportUntrustedFlow(targetType, source) {
    if (typeRequiresApprovedResponse(targetType, checker)) {
      if (!sourceHasApprovedResponseProvenance(source, targetType, checker, safetyRoot)) {
        report(source, "Untrusted value cannot flow into ApprovedResponse");
      }
    } else if (
      typeContainsApprovedResponse(targetType, checker) &&
      !sourceHasApprovedResponseContainerProvenance(source, targetType, checker, safetyRoot)
    ) {
      report(source, "Untrusted value cannot flow into an ApprovedResponse container");
    }
  }

  function visit(node) {
    if (isDynamicModuleLoaderSurface(node)) {
      report(
        node,
        "Dynamic module-loading primitives are forbidden in governed source; " +
          "introduce an ADR-reviewed allowlist before enabling one",
      );
    }
    const specifier = moduleSpecifierText(node);
    if (
      specifier !== undefined &&
      isPrivateSafetyModuleSpecifier(specifier, sourceFile, safetyRoot)
    ) {
      report(node, "The protected safety mint module cannot be imported here");
    }
    if (isForbiddenDefinition(node)) {
      report(node, "ApprovedResponse may be defined only under packages/safety");
    }
    if (ts.isFunctionLike(node) && typePredicateReferencesApprovedResponse(node.type, checker)) {
      report(node.type, "ApprovedResponse type predicates are forbidden outside packages/safety");
    }
    if (
      ts.isFunctionLike(node) &&
      (node.type === undefined || !ts.isTypePredicateNode(node.type))
    ) {
      const signature = checker.getSignatureFromDeclaration(node);
      if (
        signature !== undefined &&
        typeContainsApprovedResponse(checker.getReturnTypeOfSignature(signature), checker)
      ) {
        report(
          node.type ?? node,
          node.body === undefined
            ? "Ambient ApprovedResponse producers are forbidden outside packages/safety"
            : "ApprovedResponse producer functions are forbidden outside packages/safety",
        );
      }
    }
    if (
      ts.isVariableDeclaration(node) &&
      node.type !== undefined &&
      node.initializer === undefined &&
      typeContainsApprovedResponse(checker.getTypeFromTypeNode(node.type), checker) &&
      ts.isVariableDeclarationList(node.parent) &&
      ts.isVariableStatement(node.parent.parent) &&
      node.parent.parent.modifiers?.some(
        (modifier) => modifier.kind === ts.SyntaxKind.DeclareKeyword,
      )
    ) {
      report(node, "Ambient ApprovedResponse values are forbidden outside packages/safety");
    }
    if (
      ts.isClassDeclaration(node) ||
      ts.isClassExpression(node) ||
      ts.isInterfaceDeclaration(node)
    ) {
      for (const clause of node.heritageClauses ?? []) {
        for (const heritage of clause.types) {
          if (
            expressionReferencesAlias(heritage.expression, aliases, checker) ||
            typeNodeReferencesApprovedResponse(heritage, checker)
          ) {
            report(heritage, "ApprovedResponse inheritance is forbidden outside packages/safety");
          }
        }
      }
    }
    if (
      (ts.isNewExpression(node) || ts.isCallExpression(node)) &&
      expressionReferencesAlias(node.expression, aliases, checker)
    ) {
      report(node, "ApprovedResponse construction is forbidden outside packages/safety");
    }
    if (ts.isObjectLiteralExpression(node)) {
      const contextualType = checker.getContextualType(node);
      const actualType = checker.getTypeAtLocation(node);
      const isAssignableToApprovedResponse = approvedResponseTypes.some((approvedType) =>
        checker.isTypeAssignableTo(actualType, approvedType),
      );
      if (typeRequiresApprovedResponse(contextualType, checker) || isAssignableToApprovedResponse) {
        report(node, "ApprovedResponse object construction is forbidden outside packages/safety");
      }
    }
    if (
      (ts.isAsExpression(node) ||
        ts.isTypeAssertionExpression(node) ||
        ts.isSatisfiesExpression(node)) &&
      typeContainsApprovedResponse(checker.getTypeFromTypeNode(node.type), checker)
    ) {
      report(node, "ApprovedResponse type assertion is forbidden outside packages/safety");
    }
    if (ts.isExpression(node)) {
      reportUntrustedFlow(checker.getContextualType(node), node);
    }
    if (
      ts.isVariableDeclaration(node) &&
      node.type !== undefined &&
      node.initializer !== undefined
    ) {
      reportUntrustedFlow(checker.getTypeFromTypeNode(node.type), node.initializer);
    }
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.EqualsToken) {
      reportUntrustedFlow(checker.getTypeAtLocation(node.left), node.right);
    }
    if (ts.isCallExpression(node) || ts.isNewExpression(node)) {
      const signature = checker.getResolvedSignature(node);
      const arguments_ = node.arguments ?? [];
      if (
        node.typeArguments?.some((typeArgument) =>
          typeContainsApprovedResponse(checker.getTypeFromTypeNode(typeArgument), checker),
        )
      ) {
        report(node, "ApprovedResponse generic instantiation is forbidden outside packages/safety");
      }
      if (signature !== undefined) {
        for (
          let index = 0;
          index < arguments_.length && index < signature.parameters.length;
          index += 1
        ) {
          const argument = arguments_[index];
          const parameter = signature.parameters[index];
          if (argument !== undefined && parameter !== undefined) {
            reportUntrustedFlow(checker.getTypeOfSymbolAtLocation(parameter, argument), argument);
          }
        }
      }
      if (
        typeContainsApprovedResponse(checker.getTypeAtLocation(node), checker) &&
        !callDeclarationIsSafetyOwned(node, checker, safetyRoot)
      ) {
        report(node, "ApprovedResponse-producing calls are forbidden outside packages/safety");
      }
    }
    if (ts.isReturnStatement(node) && node.expression !== undefined) {
      let owner = node.parent;
      while (owner !== undefined && !ts.isFunctionLike(owner)) owner = owner.parent;
      if (owner !== undefined) {
        const signature = checker.getSignatureFromDeclaration(owner);
        if (signature !== undefined) {
          reportUntrustedFlow(checker.getReturnTypeOfSignature(signature), node.expression);
        }
      }
    }
    if (ts.isArrowFunction(node) && !ts.isBlock(node.body)) {
      const signature = checker.getSignatureFromDeclaration(node);
      if (signature !== undefined) {
        reportUntrustedFlow(checker.getReturnTypeOfSignature(signature), node.body);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(sourceFile);
  return violations;
}

function isTypeScriptFile(file) {
  return /\.(?:[cm]?ts|tsx)$/u.test(file);
}

function javaScriptKind(file) {
  return file.endsWith(".jsx") ? ts.ScriptKind.JSX : ts.ScriptKind.JS;
}

function collectJavaScriptStringConstants(sourceFile) {
  const constants = new Map();
  let changed = true;
  while (changed) {
    changed = false;
    for (const statement of sourceFile.statements) {
      if (
        ts.isVariableStatement(statement) &&
        (statement.declarationList.flags & ts.NodeFlags.Const) !== 0
      ) {
        for (const node of statement.declarationList.declarations) {
          if (
            !ts.isIdentifier(node.name) ||
            node.initializer === undefined ||
            constants.has(node.name.text)
          ) {
            continue;
          }
          const value = ts.isStringLiteralLike(node.initializer)
            ? node.initializer.text
            : ts.isIdentifier(node.initializer)
              ? constants.get(node.initializer.text)
              : undefined;
          if (value !== undefined) {
            constants.set(node.name.text, value);
            changed = true;
          }
        }
      }
    }
  }
  return constants;
}

function scanJavaScriptModuleBoundaries(file, safetyRoot) {
  let sourceFile;
  try {
    sourceFile = ts.createSourceFile(
      file,
      readFileSync(file, "utf8"),
      ts.ScriptTarget.Latest,
      true,
      javaScriptKind(file),
    );
  } catch (error) {
    return [
      {
        column: 1,
        file,
        line: 1,
        message: `Cannot read JavaScript source for boundary analysis: ${String(error)}`,
      },
    ];
  }

  const violations = (sourceFile.parseDiagnostics ?? []).map((diagnostic) => {
    const location =
      diagnostic.start === undefined
        ? { character: 0, line: 0 }
        : sourceFile.getLineAndCharacterOfPosition(diagnostic.start);
    return {
      column: location.character + 1,
      file,
      line: location.line + 1,
      message:
        "JavaScript source must parse for boundary analysis: " +
        ts.flattenDiagnosticMessageText(diagnostic.messageText, " "),
    };
  });
  const insideSafety = isUnder(file, safetyRoot);
  const privateSafetySource = insideSafety && isPrivateSafetySourceFile(file, safetyRoot);
  const stringConstants = collectJavaScriptStringConstants(sourceFile);

  function visit(node) {
    if (isDynamicModuleLoaderSurface(node)) {
      const location = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
      violations.push({
        column: location.character + 1,
        file,
        line: location.line + 1,
        message:
          "Dynamic module-loading primitives are forbidden in governed source; " +
          "introduce an ADR-reviewed allowlist before enabling one",
      });
    }
    const specifier = moduleSpecifierText(node, stringConstants);
    if (
      !privateSafetySource &&
      specifier !== undefined &&
      isPrivateSafetyModuleSpecifier(specifier, sourceFile, safetyRoot)
    ) {
      const location = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
      violations.push({
        column: location.character + 1,
        file,
        line: location.line + 1,
        message: insideSafety
          ? "A public JavaScript safety module cannot import or export the protected mint module"
          : "The protected safety mint module cannot be imported here",
      });
    }
    ts.forEachChild(node, visit);
  }
  visit(sourceFile);
  return violations;
}

function main() {
  const { files, safetyRoot } = parseArguments(process.argv.slice(2));
  const typeScriptFiles = files.filter(isTypeScriptFile);
  const javaScriptFiles = files.filter((file) => !isTypeScriptFile(file));
  const program = ts.createProgram(typeScriptFiles, loadCompilerOptions());
  const checker = program.getTypeChecker();
  const sourceFiles = typeScriptFiles
    .map((file) => program.getSourceFile(file))
    .filter((sourceFile) => sourceFile !== undefined);
  const approvedResponseTypes = collectApprovedResponseTypes(sourceFiles, checker, safetyRoot);
  const violations = collectCompilerDiagnostics(program, typeScriptFiles, safetyRoot);
  violations.push(
    ...typeScriptFiles.flatMap((file) => {
      const sourceFile = program.getSourceFile(file);
      return sourceFile === undefined
        ? []
        : scanSourceFile(sourceFile, checker, safetyRoot, approvedResponseTypes);
    }),
    ...javaScriptFiles.flatMap((file) => scanJavaScriptModuleBoundaries(file, safetyRoot)),
  );
  for (const violation of violations) {
    const displayPath = relative(repositoryRoot, violation.file) || violation.file;
    process.stderr.write(
      `${displayPath}:${violation.line}:${violation.column}: ${violation.message}\n`,
    );
  }
  if (violations.length > 0) process.exitCode = 1;
  else process.stdout.write("JavaScript/TypeScript architecture boundary checks passed\n");
}

try {
  main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`TypeScript boundary checker failed closed: ${message}\n`);
  process.exitCode = 1;
}

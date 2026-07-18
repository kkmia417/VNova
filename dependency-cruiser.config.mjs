/** @type {import("dependency-cruiser").IConfiguration} */
export default {
  forbidden: [
    {
      name: "no-circular-dependencies",
      severity: "error",
      from: {},
      to: { circular: true },
    },
    {
      name: "no-orphan-production-modules",
      severity: "warn",
      from: {
        orphan: true,
        pathNot: ["(^|/)index\\.ts$", "(^|/)types\\.ts$", "\\.test\\.ts$", "(^|/)generated/"],
      },
      to: {},
    },
    {
      name: "contracts-must-not-import-applications",
      severity: "error",
      from: { path: "^packages/contracts/typescript/src" },
      to: { path: "^apps/" },
    },
    {
      name: "production-must-not-import-tests",
      severity: "error",
      from: { path: "^packages/.+/src" },
      to: { path: "(^|/)(tests?|fixtures)/" },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    enhancedResolveOptions: {
      conditionNames: ["types", "import", "default"],
      exportsFields: ["exports"],
    },
    tsConfig: { fileName: "tsconfig.base.json" },
  },
};

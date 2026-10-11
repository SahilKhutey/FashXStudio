module.exports = {
  preset: "jest-expo",
  cacheDirectory: "<rootDir>/.jest-cache",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  moduleNameMapper: {
    "^react-native/setup-env$":
      "<rootDir>/node_modules/react-native/src/private/setup/setUpDefaultReactNativeEnvironment.js",
  },
};

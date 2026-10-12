import antfu from '@antfu/eslint-config'

export default antfu({
  // Third-party library code, shipped as published. Not ours to format.
  ignores: ['vendor/**'],
})

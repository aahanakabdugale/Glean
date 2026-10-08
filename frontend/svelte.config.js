/** @type {import("@sveltejs/vite-plugin-svelte").SvelteConfig} */
export default {
  compilerOptions: {
    // Keep Svelte 4-style component API (export let props, $store subscriptions,
    // on:event directives). Svelte 5 supports this via its legacy compatibility
    // layer, so all our components work without rewriting to runes.
    compatibility: {
      componentApi: 4,
    },
  },
}

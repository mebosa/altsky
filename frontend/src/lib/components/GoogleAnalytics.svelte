<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  export let id: string;

  declare global {
    interface Window {
      dataLayer: any[];
      gtag: (...args: any[]) => void;
    }
    const gtag: (...args: any[]) => void;
  }

  $: if (typeof gtag !== 'undefined') {
    gtag('config', id, {
      page_path: $page.url.pathname + $page.url.search
    });
  }

  onMount(() => {
    if (!id) return;

    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${id}`;
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    function gtag(...args: any[]) {
      window.dataLayer.push(args);
    }
    gtag('js', new Date());
    gtag('config', id);

    (window as any).gtag = gtag;
  });
</script>

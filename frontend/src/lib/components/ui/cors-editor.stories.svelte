<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import { fn } from 'storybook/test';
	import CorsEditor from './cors-editor.svelte';

	const { Story } = defineMeta({
		title: 'UI/CorsEditor',
		component: CorsEditor,
		tags: ['autodocs'],
	});
</script>

<Story name="Empty">
	{#snippet template()}
		<CorsEditor corsXml="" onsave={fn()} ondelete={fn()} />
	{/snippet}
</Story>

<Story name="With Configuration">
	{#snippet template()}
		<CorsEditor
			corsXml={`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>https://example.com</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
    <MaxAgeSeconds>3600</MaxAgeSeconds>
  </CORSRule>
</CORSConfiguration>`}
			onsave={fn()}
			ondelete={fn()}
		/>
	{/snippet}
</Story>

<Story name="Loading">
	{#snippet template()}
		<CorsEditor corsXml="" loading={true} onsave={fn()} />
	{/snippet}
</Story>

<Story name="Without Delete">
	{#snippet template()}
		<CorsEditor
			corsXml={`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
  </CORSRule>
</CORSConfiguration>`}
			onsave={fn()}
		/>
	{/snippet}
</Story>

<Story name="Custom Title">
	{#snippet template()}
		<CorsEditor
			corsXml=""
			title="Namespace CORS"
			description="Configure cross-origin resource sharing rules for this namespace."
			onsave={fn()}
		/>
	{/snippet}
</Story>

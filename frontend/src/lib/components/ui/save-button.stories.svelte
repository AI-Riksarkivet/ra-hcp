<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import SaveButton from './save-button.svelte';

	const { Story } = defineMeta({
		title: 'UI/SaveButton',
		component: SaveButton,
		tags: ['autodocs'],
		argTypes: {
			dirty: { control: 'boolean' },
			saving: { control: 'boolean' },
		},
	});
</script>

<Story name="Clean" args={{ dirty: false, saving: false, onclick: () => {} }} />

<Story name="Dirty" args={{ dirty: true, saving: false, onclick: () => {} }} />

<Story name="Saving" args={{ dirty: true, saving: true, onclick: () => {} }} />

<script>
	import { onMount } from 'svelte';
	import { websocket, wsConnected, wsError } from '../stores/simulation.js';
	import '../app.css';

	let mounted = false;

	onMount(() => {
		mounted = true;
		// WebSocket is already initialized in the store
	});
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900">
	<!-- Header -->
	<header class="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between items-center h-16">
				<div class="flex items-center space-x-4">
					<div class="flex-shrink-0">
						<h1 class="text-2xl font-bold text-white">Society Simulation</h1>
					</div>
					<div class="hidden md:block">
						<div class="ml-4 flex items-center space-x-2">
							<!-- Connection status -->
							{#if mounted}
								{#if $wsConnected}
									<div class="flex items-center space-x-1 text-green-400">
										<div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
										<span class="text-sm">Connected</span>
									</div>
								{:else}
									<div class="flex items-center space-x-1 text-red-400">
										<div class="w-2 h-2 bg-red-400 rounded-full"></div>
										<span class="text-sm">Disconnected</span>
									</div>
								{/if}
							{/if}
						</div>
					</div>
				</div>
				
				<nav class="flex space-x-4">
					<a href="/" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
						Dashboard
					</a>
					<a href="/evolution" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
						Evolution
					</a>
					<a href="/models" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
						Models
					</a>
				</nav>
			</div>
		</div>
	</header>

	<!-- Main content -->
	<main class="flex-1">
		<slot />
	</main>

	<!-- Error notifications -->
	{#if $wsError}
		<div class="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
			Connection Error: {$wsError}
		</div>
	{/if}
</div>
<script>
	import { onMount } from 'svelte';
	import { 
		simulationRunning, 
		currentIteration, 
		metrics, 
		performanceMetrics,
		models,
		simulation,
		modelManager,
		chartData
	} from '../stores/simulation.js';
	
	import SimulationCanvas from '../components/SimulationCanvas.svelte';
	import MetricsPanel from '../components/MetricsPanel.svelte';
	import ControlPanel from '../components/ControlPanel.svelte';
	import PopulationChart from '../components/PopulationChart.svelte';
	import BehaviorChart from '../components/BehaviorChart.svelte';

	let selectedModel = '';
	let speedMode = 'normal';
	let loading = false;

	onMount(async () => {
		// Load available models
		try {
			await modelManager.getModels();
			// Load current status
			const status = await simulation.getStatus();
			simulationRunning.set(status.is_running);
			selectedModel = status.current_model || '';
		} catch (error) {
			console.error('Failed to load initial data:', error);
		}
	});

	async function startSimulation() {
		if (!selectedModel) {
			alert('Please select a model first');
			return;
		}

		loading = true;
		try {
			await simulation.start(selectedModel, speedMode);
		} catch (error) {
			console.error('Failed to start simulation:', error);
			alert('Failed to start simulation');
		} finally {
			loading = false;
		}
	}

	async function pauseSimulation() {
		try {
			await simulation.pause();
		} catch (error) {
			console.error('Failed to pause simulation:', error);
		}
	}

	async function stopSimulation() {
		try {
			await simulation.stop();
		} catch (error) {
			console.error('Failed to stop simulation:', error);
		}
	}

	async function changeSpeed(newSpeed) {
		try {
			speedMode = newSpeed;
			if ($simulationRunning) {
				await simulation.changeSpeed(newSpeed);
			}
		} catch (error) {
			console.error('Failed to change speed:', error);
		}
	}
</script>

<svelte:head>
	<title>Society Simulation - Real-time Dashboard</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
	<!-- Header Stats -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
		<div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
			<div class="text-sm font-medium text-gray-400">Current Iteration</div>
			<div class="text-2xl font-bold text-white">{$currentIteration.toLocaleString()}</div>
		</div>
		
		<div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
			<div class="text-sm font-medium text-gray-400">Population</div>
			<div class="text-2xl font-bold text-green-400">{$metrics.population.alive}</div>
			<div class="text-xs text-gray-500">{$metrics.population.total} total</div>
		</div>
		
		<div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
			<div class="text-sm font-medium text-gray-400">Avg Wealth</div>
			<div class="text-2xl font-bold text-yellow-400">{$metrics.economy.avg_wealth.toFixed(1)}</div>
		</div>
		
		<div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
			<div class="text-sm font-medium text-gray-400">Performance</div>
			<div class="text-2xl font-bold text-blue-400">{$performanceMetrics.avg_fps.toFixed(1)} FPS</div>
			<div class="text-xs text-gray-500">{$performanceMetrics.iterations_per_second.toFixed(1)} IPS</div>
		</div>
	</div>

	<!-- Control Panel -->
	<div class="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
		<h2 class="text-xl font-bold text-white mb-4">Simulation Controls</h2>
		
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
			<!-- Model Selection -->
			<div>
				<label class="block text-sm font-medium text-gray-400 mb-2">Model</label>
				<select 
					bind:value={selectedModel} 
					class="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
					disabled={$simulationRunning}
				>
					<option value="">Select a model...</option>
					{#each $models as model}
						<option value={model.name}>{model.name}</option>
					{/each}
				</select>
			</div>

			<!-- Speed Control -->
			<div>
				<label class="block text-sm font-medium text-gray-400 mb-2">Speed Mode</label>
				<select 
					bind:value={speedMode} 
					on:change={() => changeSpeed(speedMode)}
					class="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="normal">Normal (1x)</option>
					<option value="fast">Fast (3x)</option>
					<option value="faster">Faster (5x)</option>
					<option value="fastest">Fastest (10x)</option>
				</select>
			</div>

			<!-- Action Buttons -->
			<div class="flex space-x-2">
				{#if !$simulationRunning}
					<button 
						on:click={startSimulation}
						disabled={loading || !selectedModel}
						class="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors"
					>
						{loading ? 'Starting...' : 'Start'}
					</button>
				{:else}
					<button 
						on:click={pauseSimulation}
						class="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded transition-colors"
					>
						Pause
					</button>
					<button 
						on:click={stopSimulation}
						class="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition-colors"
					>
						Stop
					</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- Main Dashboard -->
	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
		<!-- Simulation Canvas -->
		<div class="lg:col-span-2">
			<SimulationCanvas />
		</div>

		<!-- Side Panel -->
		<div class="space-y-6">
			<!-- Population Chart -->
			<div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
				<h3 class="text-lg font-bold text-white mb-4">Population</h3>
				<PopulationChart data={$chartData.population} />
			</div>

			<!-- Behavior Chart -->
			<div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
				<h3 class="text-lg font-bold text-white mb-4">Agent Behaviors</h3>
				<BehaviorChart data={$chartData.behaviors} />
			</div>

			<!-- Metrics Panel -->
			<MetricsPanel metrics={$metrics} performance={$performanceMetrics} />
		</div>
	</div>
</div>
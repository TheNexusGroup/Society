/**
 * Svelte stores for managing simulation state and WebSocket connection
 */

import { writable, derived } from 'svelte/store';

// WebSocket connection state
export const wsConnected = writable(false);
export const wsError = writable(null);

// Simulation state
export const simulationRunning = writable(false);
export const simulationPaused = writable(false);
export const currentIteration = writable(0);
export const currentModel = writable(null);
export const speedMode = writable('NORMAL');

// Performance metrics
export const performanceMetrics = writable({
	avg_fps: 0,
	iterations_per_second: 0,
	agents_processed: 0,
	simulation_time: 0
});

// Simulation data
export const agents = writable([]);
export const metrics = writable({
	population: { total: 0, alive: 0, dead: 0 },
	economy: { total_wealth: 0, avg_wealth: 0, total_food: 0, avg_food: 0 },
	energy: { total_energy: 0, avg_energy: 0 },
	behaviors: {},
	iteration: 0
});

// Available models
export const models = writable([]);

// Chart data (derived from metrics)
export const chartData = derived(metrics, ($metrics) => {
	return {
		population: [
			{ label: 'Alive', value: $metrics.population.alive, color: '#10B981' },
			{ label: 'Dead', value: $metrics.population.dead, color: '#EF4444' }
		],
		behaviors: Object.entries($metrics.behaviors || {}).map(([behavior, count]) => ({
			label: behavior.charAt(0).toUpperCase() + behavior.slice(1),
			value: count,
			color: getBehaviorColor(behavior)
		})),
		economy: {
			totalWealth: $metrics.economy.total_wealth || 0,
			avgWealth: $metrics.economy.avg_wealth || 0,
			totalFood: $metrics.economy.total_food || 0,
			avgFood: $metrics.economy.avg_food || 0
		}
	};
});

// WebSocket connection management
class SimulationWebSocket {
	constructor() {
		this.ws = null;
		this.reconnectAttempts = 0;
		this.maxReconnectAttempts = 5;
		this.reconnectDelay = 1000;
	}

	connect() {
		try {
			const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
			this.ws = new WebSocket(wsUrl);

			this.ws.onopen = () => {
				console.log('🔗 WebSocket connected');
				wsConnected.set(true);
				wsError.set(null);
				this.reconnectAttempts = 0;
			};

			this.ws.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					this.handleMessage(data);
				} catch (error) {
					console.error('❌ Error parsing WebSocket message:', error);
				}
			};

			this.ws.onclose = () => {
				console.log('🔌 WebSocket disconnected');
				wsConnected.set(false);
				this.attemptReconnect();
			};

			this.ws.onerror = (error) => {
				console.error('❌ WebSocket error:', error);
				wsError.set('Connection failed');
			};

		} catch (error) {
			console.error('❌ WebSocket connection error:', error);
			wsError.set('Failed to connect');
		}
	}

	handleMessage(data) {
		switch (data.type) {
			case 'simulation_update':
				currentIteration.set(data.iteration);
				if (data.metrics) {
					metrics.set(data.metrics);
					if (data.metrics.performance) {
						performanceMetrics.set(data.metrics.performance);
					}
				}
				break;

			case 'agents_data':
				agents.set(data.agents || []);
				break;

			case 'speed_change':
				speedMode.set(data.speed_mode);
				break;

			case 'status_update':
				simulationRunning.set(data.is_running || false);
				simulationPaused.set(data.is_paused || false);
				currentModel.set(data.current_model);
				speedMode.set(data.speed_mode || 'NORMAL');
				break;

			default:
				console.log('Unknown message type:', data.type);
		}
	}

	send(data) {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify(data));
		}
	}

	attemptReconnect() {
		if (this.reconnectAttempts < this.maxReconnectAttempts) {
			this.reconnectAttempts++;
			console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
			
			setTimeout(() => {
				this.connect();
			}, this.reconnectDelay * this.reconnectAttempts);
		} else {
			wsError.set('Max reconnection attempts reached');
		}
	}

	disconnect() {
		if (this.ws) {
			this.ws.close();
		}
	}

	requestAgents() {
		this.send({ type: 'request_agents' });
	}
}

// Global WebSocket instance
export const websocket = new SimulationWebSocket();

// API functions
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = {
	async get(endpoint) {
		const response = await fetch(`${API_BASE}${endpoint}`);
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		return response.json();
	},

	async post(endpoint, data) {
		const response = await fetch(`${API_BASE}${endpoint}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(data),
		});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		return response.json();
	},

	async delete(endpoint) {
		const response = await fetch(`${API_BASE}${endpoint}`, {
			method: 'DELETE',
		});
		if (!response.ok) throw new Error(`HTTP ${response.status}`);
		return response.json();
	}
};

// Simulation control functions
export const simulation = {
	async start(modelName, speedMode = 'normal') {
		return api.post('/api/simulation/control', {
			action: 'start',
			model_name: modelName,
			speed_mode: speedMode
		});
	},

	async pause() {
		return api.post('/api/simulation/control', { action: 'pause' });
	},

	async stop() {
		return api.post('/api/simulation/control', { action: 'stop' });
	},

	async reset() {
		return api.post('/api/simulation/control', { action: 'reset' });
	},

	async changeSpeed(speedMode) {
		return api.post('/api/simulation/speed', { speed_mode: speedMode });
	},

	async getStatus() {
		return api.get('/api/simulation/status');
	},

	async getMetrics() {
		return api.get('/api/simulation/metrics');
	}
};

// Model management functions
export const modelManager = {
	async getModels() {
		const result = await api.get('/api/models');
		models.set(result.models || []);
		return result.models;
	},

	async createModel(name, description, config) {
		return api.post('/api/models', { name, description, config });
	},

	async getModelInfo(modelName) {
		return api.get(`/api/models/${modelName}`);
	},

	async deleteModel(modelName) {
		return api.delete(`/api/models/${modelName}`);
	}
};

// Helper function for behavior colors
function getBehaviorColor(behavior) {
	const colors = {
		idle: '#6B7280',
		eating: '#10B981',
		working: '#3B82F6',
		resting: '#8B5CF6',
		mating: '#EC4899',
		searching: '#F59E0B',
		farming: '#84CC16',
		trading: '#06B6D4',
		socializing: '#F97316',
		dead: '#EF4444'
	};
	
	return colors[behavior] || '#6B7280';
}

// Initialize WebSocket connection
if (typeof window !== 'undefined') {
	websocket.connect();
}
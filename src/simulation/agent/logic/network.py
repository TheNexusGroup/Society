import numpy as np
import random
from typing import List, Dict, Tuple, Any

class NeuralNetwork:
    def __init__(self, input_size: int, hidden_size: int, output_size: int, learning_rate: float = 0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Initialize weights with small random values
        self.weights_input_hidden = np.random.randn(input_size, hidden_size) * 0.1
        self.weights_hidden_output = np.random.randn(hidden_size, output_size) * 0.1
        
        # Initialize biases
        self.bias_hidden = np.zeros((1, hidden_size))
        self.bias_output = np.zeros((1, output_size))
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))
    
    def sigmoid_derivative(self, x):
        return x * (1 - x)
    
    def forward(self, inputs):
        # Convert inputs to numpy array
        inputs = np.array(inputs, ndmin=2)
        
        # Calculate signals into hidden layer
        self.hidden_inputs = np.dot(inputs, self.weights_input_hidden) + self.bias_hidden
        
        # Calculate signals from hidden layer
        self.hidden_outputs = self.sigmoid(self.hidden_inputs)
        
        # Calculate signals into final output layer
        self.final_inputs = np.dot(self.hidden_outputs, self.weights_hidden_output) + self.bias_output
        
        # Calculate signals from final output layer
        self.final_outputs = self.sigmoid(self.final_inputs)
        
        return self.final_outputs
    
    def train(self, inputs, targets):
        # Forward pass
        outputs = self.forward(inputs)
        
        # Convert targets to numpy array
        targets = np.array(targets, ndmin=2)
        
        # Calculate output layer error
        output_errors = targets - outputs
        
        # Calculate hidden layer error
        hidden_errors = np.dot(output_errors, self.weights_hidden_output.T)
        
        # Update weights and biases
        # Output layer
        self.weights_hidden_output += self.learning_rate * np.dot(
            self.hidden_outputs.T, 
            output_errors * self.sigmoid_derivative(outputs)
        )
        self.bias_output += self.learning_rate * np.sum(
            output_errors * self.sigmoid_derivative(outputs), 
            axis=0
        )
        
        # Hidden layer
        self.weights_input_hidden += self.learning_rate * np.dot(
            np.array(inputs, ndmin=2).T, 
            hidden_errors * self.sigmoid_derivative(self.hidden_outputs)
        )
        self.bias_hidden += self.learning_rate * np.sum(
            hidden_errors * self.sigmoid_derivative(self.hidden_outputs), 
            axis=0
        )
    
    def save(self, filename):
        """Save network weights and biases to file"""
        np.savez(
            filename, 
            w_input_hidden=self.weights_input_hidden,
            w_hidden_output=self.weights_hidden_output,
            b_hidden=self.bias_hidden,
            b_output=self.bias_output
        )
    
    def load(self, filename):
        """Load network weights and biases from file"""
        data = np.load(filename)
        self.weights_input_hidden = data['w_input_hidden']
        self.weights_hidden_output = data['w_hidden_output']
        self.bias_hidden = data['b_hidden']
        self.bias_output = data['b_output']


class DQNetwork:
    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        # Network for Deep Q-Learning
        self.state_size = state_size
        self.action_size = action_size
        
        # Create main and target networks
        hidden_size = 24
        self.main_network = NeuralNetwork(state_size, hidden_size, action_size, learning_rate)
        self.target_network = NeuralNetwork(state_size, hidden_size, action_size, learning_rate)
        
        # Sync target with main network initially
        self.update_target_network()
        
        # Hyperparameters
        self.gamma = 0.95  # discount factor
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
    
    def update_target_network(self):
        """Update target network with weights from main network"""
        self.target_network.weights_input_hidden = self.main_network.weights_input_hidden.copy()
        self.target_network.weights_hidden_output = self.main_network.weights_hidden_output.copy()
        self.target_network.bias_hidden = self.main_network.bias_hidden.copy()
        self.target_network.bias_output = self.main_network.bias_output.copy()
    
    def encode_state(self, state_dict: Dict[str, Any]) -> List[float]:
        """Convert state dictionary to neural network input vector"""
        encoded = []
        
        # Encode energy level
        if state_dict.get('energy') == 'low':
            encoded.extend([1.0, 0.0, 0.0])
        elif state_dict.get('energy') == 'medium':
            encoded.extend([0.0, 1.0, 0.0])
        else:  # high
            encoded.extend([0.0, 0.0, 1.0])
            
        # Encode money level
        if state_dict.get('money') == 'low':
            encoded.extend([1.0, 0.0, 0.0])
        elif state_dict.get('money') == 'medium':
            encoded.extend([0.0, 1.0, 0.0])
        else:  # high
            encoded.extend([0.0, 0.0, 1.0])
            
        # Encode mood level
        if state_dict.get('mood') == 'negative':
            encoded.extend([1.0, 0.0, 0.0])
        elif state_dict.get('mood') == 'neutral':
            encoded.extend([0.0, 1.0, 0.0])
        else:  # positive
            encoded.extend([0.0, 0.0, 1.0])
            
        # Encode corruption level
        if state_dict.get('corruption') == 'low':
            encoded.extend([1.0, 0.0, 0.0])
        elif state_dict.get('corruption') == 'medium':
            encoded.extend([0.0, 1.0, 0.0])
        else:  # high
            encoded.extend([0.0, 0.0, 1.0])
            
        # Encode food reserves level
        if state_dict.get('food_reserves') == 'low':
            encoded.extend([1.0, 0.0, 0.0])
        elif state_dict.get('food_reserves') == 'medium':
            encoded.extend([0.0, 1.0, 0.0])
        else:  # high
            encoded.extend([0.0, 0.0, 1.0])
            
        # Encode farm knowledge (0 for no knowledge, 1 for knowledge)
        encoded.append(1.0 if state_dict.get('knows_farm_location', False) else 0.0)
        encoded.append(1.0 if state_dict.get('knows_yield_farm', False) else 0.0)
        
        # Encode workplace knowledge
        encoded.append(1.0 if state_dict.get('knows_workplace', False) else 0.0)
        
        # Encode social factors (0 for no social connections, 1 for active connections)
        encoded.append(1.0 if state_dict.get('has_trading_partners', False) else 0.0)
        
        return encoded
    
    def select_action(self, state: Dict[str, Any], exploration_rate: float = None) -> int:
        """Select action using epsilon-greedy policy"""
        if exploration_rate is None:
            exploration_rate = self.epsilon
            
        if random.random() < exploration_rate:
            return random.randint(0, self.action_size - 1)
        else:
            # Convert state to network input
            state_vector = self.encode_state(state)
            
            # Get Q-values from network
            q_values = self.main_network.forward(state_vector)
            
            # Return action with highest Q-value
            return np.argmax(q_values)
    
    def train(self, state, action, reward, next_state, done):
        """Train the network with a single experience"""
        state_vector = self.encode_state(state)
        next_state_vector = self.encode_state(next_state)
        
        # Get current Q values
        current_q = self.main_network.forward(state_vector)
        
        # Get next Q values from target network
        next_q = self.target_network.forward(next_state_vector)
        
        # Update target for the specific action
        target = current_q.copy()
        
        # Ensure action is an integer index
        if isinstance(action, str):
            # Convert string action to index if needed
            action_idx_map = {
                'eat': 0, 'work': 1, 'rest': 2, 'mate': 3, 'search': 4,
                'plant-food': 5, 'harvest-food': 6, 'gift-food': 7, 'gift-money': 8,
                'invest': 9, 'buy-food': 10, 'sell-food': 11,
                'trade-food-for-money': 12, 'trade-money-for-food': 13
            }
            action_idx = action_idx_map.get(action, 0)  # Default to 0 if unknown
        else:
            action_idx = action
        
        if done:
            target[0][action_idx] = reward
        else:
            target[0][action_idx] = reward + self.gamma * np.max(next_q)
        
        # Train the main network
        self.main_network.train(state_vector, target)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def get_action_values(self, state_dict):
        """Get action values (Q-values) for a given state"""
        # Convert state dictionary to neural network input vector
        state_vector = self.encode_state(state_dict)
        
        # Get Q-values from main network
        q_values = self.main_network.forward(state_vector)
        
        # Return the raw values
        return q_values[0]  # Return the first (and only) row of outputs

    def train_batch(self, experiences):
        """Train network with a batch of experiences"""
        if not experiences:
            return
        
        # Process a batch of experiences
        for exp in experiences:
            state = exp.state
            action = exp.action
            reward = exp.reward
            next_state = exp.next_state
            done = exp.done
            
            # Train with individual experience
            self.train(state, action, reward, next_state, done)
        
        # After batch is processed, update target network if needed
        return

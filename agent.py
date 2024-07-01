import torch
from collections import deque
import random
import numpy as np
from opt_einsum.backends import torch
from gameAI import GameAI

MAX_MEM = 400000
BATCH_SIZE = 2000

learning_rate = 0.01


class Agent:
    def __init__(self):
        self.num_games = 0
        self.epsilon = 0
        self.epsilon_decay = 0.995
        self.memory = deque(maxlen=MAX_MEM)
        self.model = None
        self.trainer = None

    def get_state(self, game):
        state = game.get_states()
        print(state)
        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long(self):
        if len(self.memory) > BATCH_SIZE:
            minibatch = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_batch = self.memory

        states, actions, rewards, next_states, dones = zip(*minibatch)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        self.epsilon = 100 - self.num_games
        final_move = [0, 0, 0, 0]

        if np.random.rand() < self.epsilon/100:
            move = random.randint(0, 3)
            final_move[move] = 1
        else:
            state00 = torch.tensor(state, dtype=torch.float)
            pred = self.model(state00)
            move = torch.argmax(pred).item()
            final_move[move] = 1

        return final_move


def train():
    plot_score = []
    plot_mean = []
    record = -1

    last_10_scores = deque(maxlen=10)

    agent = Agent()
    game = GameAI()

    while True:
        first_state = agent.get_state(game)
        move = agent.get_action(first_state)
        print(move)
        reward, done, score = game.play_action(move)

        second_state = agent.get_state(game)
        agent.train_short(first_state, move, reward, second_state, done)
        agent.remember(first_state, move, reward, second_state, done)

        if done:
            game.reset_game()
            agent.num_games += 1
            agent.train_long()

            if score > record:
                record = score
                agent.model.save_model()

            print(f"Game number : {agent.num_games}, Score : {score}, Record : {record}")
            plot_score.append(score)
            last_10_scores.append(score)
            mean_score = np.mean(last_10_scores)
            plot_mean.append(mean_score)


if __name__ == '__main__':
    train()

# -*- coding: utf-8 -*-

import copy
import numpy as np
from chainer import cuda, FunctionSet, Variable, optimizers
import chainer.functions as F
import random


class QNet:
    # Hyper-Parameters
    gamma = 0.99                            # Discount factor
    initial_exploration = 5*10**4             # Initial exploratoin. original: 5x10^4
    replay_size = 32                        # Replay (batch) size
    target_model_update_freq = 10**4        # Target update frequancy. original: 10^4
    data_size = 10**6                       # Data size of history. original: 10^6
    hist_size = 1                           #original: 4
    num_of_actions = 2 ## CDQN

    def __init__(self, use_gpu, dim):
        self.use_gpu = use_gpu
        #self.num_of_actions = len(enable_controller)
        #self.enable_controller = enable_controller
        self.dim = dim
        self.num_of_states = self.dim*self.hist_size

        print("Initializing Q-Network...")

        self.critic = FunctionSet(
            l1=F.Linear(self.num_of_actions+self.num_of_states, 1024),
            l2=F.Linear(1024,512),
            l3=F.Linear(512,256),
            l4=F.Linear(256,128),
            q_value=F.Linear(128,1,initialW=np.zeros((1,128),dtype=np.float32))
        )

        self.actor = FunctionSet(
            l1=F.Linear(self.num_of_states,1024),
            l2=F.Linear(1024,512),
            l3=F.Linear(512,256),
            l4=F.Linear(256,128),
            a_value=F.Linear(128,self.num_of_actions,initialW=np.zeros((1,128),dtype=np.float32))
        )
        # hidden_dim = 256
        # self.model = FunctionSet(
        #     l4=F.Linear(self.dim*self.hist_size, hidden_dim, wscale=np.sqrt(2)),
        #     q_value=F.Linear(hidden_dim, self.num_of_actions,
        #                      initialW=np.zeros((self.num_of_actions, hidden_dim),
        #                                        dtype=np.float32))
        # )
        if self.use_gpu >= 0:
            #self.model.to_gpu()
            self.critic.to_gpu()
            self.actor.to_gpu()

        #self.model_target = copy.deepcopy(self.model)

        self.critic_target = copy.deepcopy(self.critic)
        self.actor_target = copy.deepcopy(self.actor)

        #self.optimizer = optimizers.RMSpropGraves(lr=0.00025, alpha=0.95, momentum=0.95, eps=0.0001)
        #self.optimizer.setup(self.model.collect_parameters())

        self.optim_critic = optimizers.Adam(alpha=0.00001)
        self.optim_actor = optimizers.Adam(alpha=0.00001)
        self.optim_critic.setup(self.critic)
        self.optim_actor.setup(self.actor)

        # History Data :  D=[s, a, r, s_dash, end_episode_flag]
        # self.d = [np.zeros((self.data_size, self.hist_size, self.dim), dtype=np.uint8),
        #           np.zeros(self.data_size, dtype=np.uint8),
        #           np.zeros((self.data_size, 1), dtype=np.int8),
        #           np.zeros((self.data_size, self.hist_size, self.dim), dtype=np.uint8),
        #           np.zeros((self.data_size, 1), dtype=np.bool)]
        self.d = [np.zeros((self.data_size, self.num_of_states), dtype=np.float32),
                  np.zeros((self.data_size, self.num_of_actions), dtype=np.float32),
                  np.zeros((self.data_size, 1), dtype=np.float32),
                  np.zeros((self.data_size, self.num_of_states), dtype=np.float32),
                  np.zeros((self.data_size, 1), dtype=np.bool)]

    def forward(self, state, action, reward, state_dash, episode_end):
        num_of_batch = state.shape[0]
        # s = Variable(state)
        # s_dash = Variable(state_dash)
        s = Variable(cuda.to_gpu(np.concatenate([state, action],1)))
        s_dash = Variable(cuda.to_gpu(state_dash))

        q = self.q_func(s)  # Get Q-value

        # Generate Target Signals
        # tmp = self.q_func_target(s_dash)  # Q(s',*)
        # if self.use_gpu >= 0:
        #     tmp = list(map(np.max, tmp.data.get()))  # max_a Q(s',a)
        # else:
        #     tmp = list(map(np.max, tmp.data))  # max_a Q(s',a)
        #
        # max_q_dash = np.asanyarray(tmp, dtype=np.float32)
        # if self.use_gpu >= 0:
        #     target = np.asanyarray(q.data.get(), dtype=np.float32)
        # else:
        #     # make new array
        #     target = np.array(q.data, dtype=np.float32)
        action_dash_tmp = self.a_func_target(s_dash)
        action_dash = np.asanyarray(action_dash_tmp.data.get(), dtype=np.float32)
        tmp_dash = Variable(cuda.to_gpu(np.concatenate([state_dash, action_dash],1)))
        Q_dash_tmp = self.q_func_target(tmp_dash)
        Q_dash = np.asanyarray(Q_dash_tmp.data.get(), dtype=np.float32)
        target = np.asanyarray(q.data.get(), dtype=np.float32)

        for i in xrange(num_of_batch):
            if not episode_end[i][0]:
                tmp_ = reward[i] + self.gamma * Q_dash[i]#max_q_dash[i]
            else:
                tmp_ = reward[i]

            # action_index = self.action_to_index(action[i])
            # target[i, action_index] = tmp_
            target[i] = tmp_

        # TD-error clipping
        if self.use_gpu >= 0:
            target = cuda.to_gpu(target)
        td = Variable(target) - q #q  # TD error
        td_tmp = td.data + 1000.0 * (abs(td.data) <= 1)  # Avoid zero division
        td_clip = td * (abs(td.data) <= 1) + td/abs(td_tmp) * (abs(td.data) > 1)

        #zero_val = np.zeros((self.replay_size, self.num_of_actions), dtype=np.float32)
        zero_val = np.zeros((self.replay_size, 1), dtype=np.float32)
        if self.use_gpu >= 0:
            zero_val = cuda.to_gpu(zero_val)
        zero_val = Variable(zero_val)
        loss = F.mean_squared_error(td_clip, zero_val)
        return loss, q

    def stock_experience(self, time,
                        state, action, reward, state_dash,
                        episode_end_flag):
        data_index = time % self.data_size

        if episode_end_flag is True:
            self.d[0][data_index] = state
            self.d[1][data_index] = action
            self.d[2][data_index] = reward
        else:
            self.d[0][data_index] = state
            self.d[1][data_index] = action
            self.d[2][data_index] = reward
            self.d[3][data_index] = state_dash
        self.d[4][data_index] = episode_end_flag

    def experience_replay(self, time):
        if self.initial_exploration < time:
            # Pick up replay_size number of samples from the Data
            if time < self.data_size:  # during the first sweep of the History Data
                replay_index = np.random.randint(0, time, (self.replay_size, 1))
            else:
                replay_index = np.random.randint(0, self.data_size, (self.replay_size, 1))

            s_replay = np.ndarray(shape=(self.replay_size, self.num_of_states), dtype=np.float32)
            a_replay = np.ndarray(shape=(self.replay_size, self.num_of_actions), dtype=np.float32)
            r_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.float32)
            s_dash_replay = np.ndarray(shape=(self.replay_size, self.num_of_states), dtype=np.float32)
            # s_replay = np.ndarray(shape=(self.replay_size, self.hist_size, self.dim), dtype=np.float32)
            # a_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.uint8)
            # r_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.float32)
            # s_dash_replay = np.ndarray(shape=(self.replay_size, self.hist_size, self.dim), dtype=np.float32)
            episode_end_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.bool)
            for i in xrange(self.replay_size):
                s_replay[i] = np.asarray(self.d[0][replay_index[i]], dtype=np.float32)
                a_replay[i] = np.asarray(self.d[1][replay_index[i]], dtype=np.float32)
                #a_replay[i] = self.d[1][replay_index[i]]
                r_replay[i] = self.d[2][replay_index[i]]
                s_dash_replay[i] = np.array(self.d[3][replay_index[i]], dtype=np.float32)
                episode_end_replay[i] = self.d[4][replay_index[i]]

            # Gradient-based critic update
            self.optim_critic.zero_grads()
            loss, q = self.forward(s_replay, a_replay, r_replay, s_dash_replay, episode_end_replay)
            loss.backward()
            self.optim_critic.update()

            # Update the actor
            self.optim_critic.zero_grads()
            self.optim_actor.zero_grads()
            self.updateActor(s_replay)

            self.soft_target_model_update()

            print "AVG_Q %f" % (np.average(q.data.get()))
            print("loss " + str(loss.data))
            # if self.use_gpu >= 0:
            #     s_replay = cuda.to_gpu(s_replay)
            #     s_dash_replay = cuda.to_gpu(s_dash_replay)
            #
            # # Gradient-based update
            # self.optimizer.zero_grads()
            # loss, _ = self.forward(s_replay, a_replay, r_replay, s_dash_replay, episode_end_replay)
            # loss.backward()
            # self.optimizer.update()

    def q_func(self, state):
        h1 = F.relu(self.critic.l1(state))
        h2 = F.relu(self.critic.l2(h1))
        h3 = F.relu(self.critic.l3(h2))
        h4 = F.relu(self.critic.l4(h3))
        Q = self.critic.q_value(h4)
        return Q

    def q_func_target(self, state):
        h1 = F.relu(self.critic_target.l1(state))
        h2 = F.relu(self.critic_target.l2(h1))
        h3 = F.relu(self.critic_target.l3(h2))
        h4 = F.relu(self.critic.l4(h3))
        Q = self.critic_target.q_value(h4)
        return Q

    # def q_func(self, state):
    #     h4 = F.relu(self.model.l4(state / 255.0))
    #     q = self.model.q_value(h4)
    #     return q
    #
    # def q_func_target(self, state):
    #     h4 = F.relu(self.model_target.l4(state / 255.0))
    #     q = self.model_target.q_value(h4)
    #     return q

    def a_func(self, state):
        h1 = F.relu(self.actor.l1(state))
        h2 = F.relu(self.actor.l2(h1))
        h3 = F.relu(self.actor.l3(h2))
        h4 = F.relu(self.actor.l4(h3))
        A = self.actor.a_value(h4)
        return A

    def a_func_target(self, state):
        h1 = F.relu(self.actor_target.l1(state))
        h2 = F.relu(self.actor_target.l2(h1))
        h3 = F.relu(self.actor_target.l3(h2))
        h4 = F.relu(self.actor.l4(h3))
        A = self.actor_target.a_value(h4)
        return A

    def e_greedy(self, state, epsilon):
        s = Variable(state)
        a = self.a_func(s)
        a = a.data
        # q = self.q_func(s)
        # q = q.data

        if np.random.rand() < epsilon:
            #action = np.random.uniform(-1.,1.,(1,self.num_of_actions)).astype(np.float32)
            action = np.zeros((1,2))
            action[0][0] = random.random()
            action[0][1] = random.uniform(-1.,1.)
            #index_action = np.random.randint(0, self.num_of_actions)
            print(" Random"),
        else:
            action = a.get()
            # if self.use_gpu >= 0:
            #     index_action = np.argmax(q.get())
            # else:
            #     index_action = np.argmax(q)
            print("#Greedy"),
        return action #self.index_to_action(index_action), q

    def hard_target_model_update(self):
        self.critic_target = copy.deepcopy(self.critic)
        self.actor_target = copy.deepcopy(self.actor)

    def soft_target_model_update(self, tau=0.001):
        self.critic_target.l1.W.data = tau*self.critic.l1.W.data + (1-tau)*self.critic_target.l1.W.data
        self.critic_target.l2.W.data = tau*self.critic.l2.W.data + (1-tau)*self.critic_target.l2.W.data
        self.critic_target.l3.W.data = tau*self.critic.l3.W.data + (1-tau)*self.critic_target.l3.W.data
        self.critic_target.l4.W.data = tau*self.critic.l4.W.data + (1-tau)*self.critic_target.l4.W.data
        self.critic_target.q_value.W.data = tau*self.critic.q_value.W.data + (1-tau)*self.critic_target.q_value.W.data
        self.actor_target.l1.W.data = tau*self.actor.l1.W.data + (1-tau)*self.actor_target.l1.W.data
        self.actor_target.l2.W.data = tau*self.actor.l2.W.data + (1-tau)*self.actor_target.l2.W.data
        self.actor_target.l3.W.data = tau*self.actor.l3.W.data + (1-tau)*self.actor_target.l3.W.data
        self.actor_target.l4.W.data = tau*self.actor.l4.W.data + (1-tau)*self.actor_target.l4.W.data
        self.actor_target.a_value.W.data = tau*self.actor.a_value.W.data + (1-tau)*self.actor_target.a_value.W.data

    # def target_model_update(self):
    #     self.model_target = copy.deepcopy(self.model)
    #
    # def index_to_action(self, index_of_action):
    #     return self.enable_controller[index_of_action]
    #
    # def action_to_index(self, action):
    #     return self.enable_controller.index(action)

    def updateActor(self, state):
        num_of_batch = state.shape[0]
        A_max = 1.0
        A_min = -1.0

        A = self.a_func(Variable(cuda.to_gpu(state)))
        tmp = Variable(cuda.to_gpu(np.concatenate([state, A.data.get()], 1)))
        Q = self.q_func(tmp)

        # Backward prop towards actor net
        # self.critic.zerograds()
        # self.actor.zerograds()
        Q.grad = cuda.to_gpu(np.ones((num_of_batch, 1), dtype=np.float32) * (-1.0))
        #        Q.grad = Q.data*(-1.0)
        Q.backward()
        A.grad = tmp.grad[:, -self.num_of_actions:]
        print("sample_A.grad: " + str(A.grad[0]))
        for i in xrange(num_of_batch):
            for j in xrange(self.num_of_actions):
                if A.grad[i][j] < 0:
                    A.grad[i][j] *= (A_max - A.data[i][j]) / (A_max - A_min)
                elif A.grad[i][j] > 0:
                    A.grad[i][j] *= (A.data[i][j] - A_min) / (A_max - A_min)

        A.backward()
        self.optim_actor.update()
        print("sample_A.grad: " + str(A.grad[0]))
from singleton import Singleton

from cnn_dqn_agent import CnnDqnAgent

import io
from PIL import Image
from PIL import ImageOps
import threading
import numpy as np

from gene_generator import GeneGenerator

#@Singleton
class Agent:
    agent_initialized = False
    ga    = GeneGenerator()      # add Naka
    agent_id = -1                # add Naka
    cycle_counter = 0
    thread_event = threading.Event()
    reward_sum = 0
    depth_image_dim = 32 * 32
    depth_image_count = 1
    gene_count = 3 # Number of gene (add Naka)

    def __init__(self, args):
        print "start to load cnn model"
        self.args = args
        self.cnnDqnAgent = CnnDqnAgent(
            use_gpu=self.args.gpu,
            depth_image_dim=self.depth_image_dim * self.depth_image_count)
        print 'finish loading cnn model'
        self.cnnDqnAgent.agent_init()
        print 'finish init cnn dqn agent'

    def received_message(self, agentServer, dat):
        image = []
        for i in xrange(self.depth_image_count):
            image.append(Image.open(io.BytesIO(bytearray(dat['image'][i]))))
        depth = []
        for i in xrange(self.depth_image_count):
            d = (Image.open(io.BytesIO(bytearray(dat['depth'][i]))))
            depth.append(np.array(ImageOps.grayscale(d)).reshape(self.depth_image_dim))

        observation = {"image": image, "depth": depth}
        gene = []  # add Naka
        for i in xrange(len(dat['gene'])):
            gene.append(dat['gene'][i])
        reward = dat['reward']
        rewards  = dat['rewards']  # add Naka
        self.agent_id = dat['agent_id'] # add Naka
        end_episode = dat['endEpisode']

        if not self.agent_initialized:
            print 'connected and agent started..'
            self.agent_initialized = True
            action = self.cnnDqnAgent.agent_start(observation)
            agentServer.send_action(action)
            with open(self.args.log_file, 'w') as the_file:
                the_file.write('cycle, episode_reward_sum \n')
        else:
            self.thread_event.wait()
            self.cycle_counter += 1
            self.reward_sum += reward

            if end_episode:
                self.cnnDqnAgent.agent_end(reward)
                action = self.cnnDqnAgent.agent_start(observation)  # TODO
                self.gene = self.ga.gene_updater(gene, rewards) # add Naka
                print self.agent_id, self.gene
                agentServer.send_actionAndgene(action, self.gene[self.agent_id]) # add Naka
                with open(self.args.log_file, 'a') as the_file:
                    the_file.write(str(self.cycle_counter) +
                                   ',' + str(self.reward_sum) + '\n')
                self.reward_sum = 0
            else:
                action, eps, obs_array = self.cnnDqnAgent.agent_step(reward, observation)
                agentServer.send_action(action)
                self.cnnDqnAgent.agent_step_update(reward, action, eps, obs_array)

        self.thread_event.set()



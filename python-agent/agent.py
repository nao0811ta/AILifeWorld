from singleton import Singleton

from cnn_dqn_agent import CnnDqnAgent

import io
from PIL import Image
from PIL import ImageOps
import threading
import numpy as np

#@Singleton
class Agent:
    cnnDqnAgent = CnnDqnAgent()
    agent_initialized = False
    cycle_counter = 0
    thread_event = threading.Event()
    reward_sum = 0
    depth_image_dim = 32 * 32
    depth_image_count = 1

    def __init__(self, args):
        print "init first agent"
        self.args = args

    def received_message(self, agentServer, dat):
        image = []
        for i in xrange(self.depth_image_count):
            image.append(Image.open(io.BytesIO(bytearray(dat['image'][i]))))
        depth = []
        for i in xrange(self.depth_image_count):
            d = (Image.open(io.BytesIO(bytearray(dat['depth'][i]))))
            depth.append(np.array(ImageOps.grayscale(d)).reshape(self.depth_image_dim))

        observation = {"image": image, "depth": depth}
        reward = dat['reward']
        end_episode = dat['endEpisode']

        if not self.agent_initialized:
            self.agent_initialized = True
            print ("initializing agent...gpu count : " + str(self.args.gpu))
            self.cnnDqnAgent.agent_init(
                use_gpu=self.args.gpu,
                depth_image_dim=self.depth_image_dim * self.depth_image_count)

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
                agentServer.send_action(action)
                with open(self.args.log_file, 'a') as the_file:
                    the_file.write(str(self.cycle_counter) +
                                   ',' + str(self.reward_sum) + '\n')
                self.reward_sum = 0
            else:
                action, eps, q_now, obs_array = self.cnnDqnAgent.agent_step(reward, observation)
                agentServer.send_action(action)
                self.cnnDqnAgent.agent_step_update(reward, action, eps, q_now, obs_array)

        self.thread_event.set()
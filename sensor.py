import numpy as np
import random
from motion_model import motion_model
from motion_init_object import motion_init_object

import matplotlib.pyplot as plt



class sensor(motion_model,motion_init_object):
    def __init__(self,type):
        motion_model.__init__(self,1)
        motion_init_object.__init__(self)

        initial_location = [self.init_x,self.init_y]
        #initial_location = [X, Y]
        mean_x_vel = self.init_xdot
        mean_y_vel = self.init_ydot
        mean_x_acc = self.init_xdotdot
        mean_y_acc = self.init_ydotdot
        x_var = self.x_var
        y_var = self.y_var

        self.initial_location = initial_location
        self.current_location = self.initial_location
        self.historical_location = [self.initial_location]

        self.initial_velocity = [mean_x_vel, mean_y_vel]
        self.current_velocity = self.initial_velocity
        self.historical_velocity = [self.initial_velocity]
        self.x_var = x_var
        self.y_var = y_var

        #For constant accelaration model
        self.initial_acc = [mean_x_acc, mean_y_acc]
        self.current_acc = self.initial_acc
        self.historical_acc = [self.initial_acc]

        #For constant-turn model
        self.initial_speed = [self.init_speed]
        self.current_speed = self.initial_speed
        self.historical_speed = [self.initial_speed]

        self.initial_heading = [self.init_heading]
        self.current_heading = self.initial_heading
        self.historical_heading = [self.initial_heading]

        #generate an initial command

        self.initial_command = np.random.multinomial(1,np.array([1,1,1])/3.0).argmax()
        #current command
        self.current_command = self.initial_command
        self.historical_command = [self.initial_command]

        self.motion_type = type
        self.sensor_actions = []

    def sigmoid(self,x, derivative=False):
        return self.sigmoid(x) * (1 - self.sigmoid(x)) if derivative else 1 / (1 + np.exp(-x))

    def plot_sensor_trajectory(self):
        x = []
        y = []
        [x.append(z[0]) for z in self.historical_location]
        [y.append(z[1]) for z in self.historical_location]
        plot1, = plt.plot(x,y,"bs-",linewidth=3)
        plt.xlabel("x",size=15)
        plt.ylabel("y",size=15)
        plt.grid(True)
        plt.show()

    def generate_action(self,params,state,sigma):
        if self.motion_type==self.policy_command_type_linear:
            weight = params[0]['weight']
            Delta = np.random.normal(weight.dot(state), sigma)
            return (Delta)
        elif self.motion_type==self.policy_command_type_RBF:
            weight = params[1]['weight']
            Delta = np.random.normal(weight.dot(state), sigma)
            return (Delta)

        elif self.motion_type==self.policy_command_type_MLP:
            weight1 = params[2]['weight1']
            weight2 = params[2]['weight2']
            bias1 = params[2]['bias1']
            bias2 = params[2]['bias2']

            layer1_output = self.sigmoid(weight1.dot(state)+bias1)
            layer2_output = weight2.dot(layer1_output)+bias2
            Delta = np.random.normal(layer2_output.reshape([2]),sigma)

            return (Delta)

    def update_location_decentralized(self,actions):

        final_action = np.mean(actions,axis=0)
        self.sensor_actions.append(final_action)
        new_x = self.current_location[0] + final_action[0]
        new_y = self.current_location[1] + final_action[1]
        self.current_location = [new_x, new_y]
        self.historical_location.append(self.current_location)


    def update_location_new(self,params,state,sigma):

        if self.motion_type==self.policy_command_type_linear:
            weight = params[0]['weight']
            Delta = np.random.normal(weight.dot(state), sigma)
            self.sensor_actions.append(Delta)
            # Delta = np.random.normal(np.zeros([2]),sigma)
            new_x = self.current_location[0] + Delta[0]
            new_y = self.current_location[1] + Delta[1]
            self.current_location = [new_x, new_y]
            self.historical_location.append(self.current_location)
            return (None)
        elif self.motion_type==self.policy_command_type_RBF:
            weight = params[1]['weight']
            Delta = np.random.normal(weight.dot(state), sigma)
            self.sensor_actions.append(Delta)
            # Delta = np.random.normal(np.zeros([2]),sigma)
            new_x = self.current_location[0] + Delta[0]
            new_y = self.current_location[1] + Delta[1]
            self.current_location = [new_x, new_y]
            self.historical_location.append(self.current_location)
            return (None)

        elif self.motion_type==self.policy_command_type_MLP:
            weight1 = params[2]['weight1']
            weight2 = params[2]['weight2']
            bias1 = params[2]['bias1']
            bias2 = params[2]['bias2']

            layer1_output = self.sigmoid(weight1.dot(state)+bias1)
            layer2_output = weight2.dot(layer1_output)+bias2
            Delta = np.random.normal(layer2_output.reshape([2]),sigma)
            self.sensor_actions.append(Delta)
            # Delta = np.random.normal(np.zeros([2]),sigma)
            new_x = self.current_location[0] + Delta[0]
            new_y = self.current_location[1] + Delta[1]
            self.current_location = [new_x, new_y]
            self.historical_location.append(self.current_location)
            return (layer1_output)

        elif self.motion_type==self.policy_command_type_RANDOM:
            Delta = np.random.normal(np.zeros([2]), sigma)
            self.sensor_actions.append(Delta)
            # Delta = np.random.normal(np.zeros([2]),sigma)
            new_x = self.current_location[0] + Delta[0]
            new_y = self.current_location[1] + Delta[1]
            self.current_location = [new_x, new_y]
            self.historical_location.append(self.current_location)
            return (None)





    def update_location(self,weight,sigma,state):

        new_command = np.random.multinomial(1,np.array([1,1,1])/3.0).argmax()
        A,B = self.binary_command(new_command)

        if self.motion_type==self.constant_turn_type:
            #generate values for both the heading and speed
            heading = self.heading_rate

            #This is constant-turn model
            new_x = self.current_location[0] + self.T*self.current_speed[0]*np.cos(heading)
            new_y = self.current_location[1] + self.T*self.current_speed[0]*np.sin(heading)
            new_speed = self.current_speed[0] + self.speed_std*np.sqrt(self.T)*np.random.normal(0,1)
            #new_heading = self.current_heading[0] + self.heading_std*np.sqrt(self.T)*np.random.normal(0,1)
            new_heading = heading

            self.current_location = [new_x,new_y]
            self.current_speed = [new_speed]
            self.current_heading = [new_heading]
            self.historical_location.append(self.current_location)
            self.historical_speed.append(self.current_speed)
            self.historical_heading.append(self.current_heading)
        elif self.motion_type==self.policy_command_type:
            Delta =  np.random.normal(weight.dot(state),sigma)
            self.sensor_actions.append(Delta)
            #Delta = np.random.normal(np.zeros([2]),sigma)
            new_x = self.current_location[0] + Delta[0]
            new_y = self.current_location[1] + Delta[1]

            self.current_location = [new_x,new_y]
            self.historical_location.append(self.current_location)
        else:
            if self.motion_type==self.constant_velocity_type:
                A,B = self.constant_velocity(self.heading_rate)
            elif self.motion_type==self.constant_accelaration_type:
                A, B = self.constant_accelaration()

            noise_x = np.random.normal(0,self.x_var)
            noise_y = np.random.normal(0,self.y_var)

            if self.motion_type == self.constant_accelaration_type:
                current_state = [self.current_location[0], self.current_location[1], self.current_velocity[0],
                                 self.current_velocity[1],self.current_acc[0],self.current_acc[1]]
            else:
                current_state = [self.current_location[0], self.current_location[1], self.current_velocity[0],
                                self.current_velocity[1]]
            new_state = A.dot(current_state) + B.dot(np.array([noise_x, noise_y]))  # This is the new state

            new_location = [new_state[0], new_state[1]]
            self.current_location = new_location
            self.historical_location.append(self.current_location)

            new_velocity = [new_state[2], new_state[3]]
            self.current_velocity = new_velocity
            self.historical_velocity.append(self.current_velocity)

            if self.motion_type == self.constant_accelaration_type:
                new_acc = [new_state[4], new_state[5]]
                self.current_acc = new_acc
                self.historical_acc.append(self.current_acc)

            self.current_command = new_command
            self.historical_command.append(new_command)

if __name__=="__main__":
    s = sensor([500,500],3,-2,.01,.01)

    for n in range(0,500):
        s.update_location()

    




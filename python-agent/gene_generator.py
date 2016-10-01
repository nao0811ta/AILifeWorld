import random

from deap import base
from deap import creator
from deap import tools


class GeneGenerator:
    def __init__(self):
        self.gene=[]
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()

        self.toolbox.register("attr_paramater", random.randint, 1, 30)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, 
                         self.toolbox.attr_paramater, 3)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        def evalMax(rewards):
            return rewards,
        self.toolbox.register("evaluate", evalMax)
        self.toolbox.register("mate", tools.cxOnePoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=1.0, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=2)

    def gene_generator(self, n):
        gene = self.toolbox.population(n=n)
        return gene

    def gene_updater(self, gene, rewards):
        self.gene = [creator.Individual(i) for i in gene]
        # CXPB  is the probability with which two individuals
        #       are crossed
        #
        # MUTPB is the probability for mutating an individual
        #
        # NGEN  is the number of generations for which the
        #       evolution runs
        CXPB, MUTPB, NGEN = 0.8, 0.4, 1
    
        # Evaluate the entire population
        fitnesses = list(map(self.toolbox.evaluate, rewards))
        for ind, fit in zip(self.gene, fitnesses):
            ind.fitness.values = fit

        # Begin the evolution
        for g in range(NGEN):
            # Select the next generation individuals
            offspring = self.toolbox.select(self.gene, len(self.gene))
            # Clone the selected individuals
            offspring = list(map(self.toolbox.clone, offspring))
    
            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):

                # cross two individuals with probability CXPB
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)

                    # fitness values of the children
                    # must be recalculated later
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:

                # mutate an individual with probability MUTPB
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values
    
            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, rewards)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
        
            # The population is entirely replaced by the offspring
            self.gene[:] = offspring
        
        return self.gene

if __name__ == "__main__":
    gene = GeneGenerator().gene_generator(3)
    GeneGenerator().gene_updater([[23,44,55], [3,44,5], [55,34,66]], [50,25,30])


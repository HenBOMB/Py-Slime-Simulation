import simulation
import json

path = "configs/a1.json"

simulation.run(json.load(open(path)))

# # Slime Simulation Paper -> 
# # https://uwe-repository.worktribe.com/output/980579

# # The amount of agents to simulate, must always be bigger than 16
# AGENT_COUNT = config["agent_count"]

# # Instead of the above, use a percentage relative to the amount of pixels on the screen to determine the amount of agents
# # PERCENT = 15
# # AGENT_COUNT = math.floor(PERCENT / 100 * WIDTH * HEIGHT)

# # How many times to compute the simulation per frame
# STEPS_PER_FRAME = config["steps_per_frame"]

# # The postion the agents start the simulation in
# # 0: random position and angle
# # 1: all at the center with andom angle
# # 2: random point in a circle with random mangle
# # 3: random point in a circle with angle heading towards the center
# # 4: random point in a circle rim with angle heading towards the center
# STARTING_MODE = config["starting_mode"]

# # Make the agents die if they get trapped and cannot move or join another one of their species path
# # Or if they collide with other species
# DIE_ON_TRAPPED = config["die_on_trapped"]

# # Agents will start dying after DEATH_TIME seconds, this is to give them some time to spread out
# DEATH_TIME = config["death_time"]

# # Does additional checks with the attempt of never colliding with other species (forces the agent to avoid other species as much as possible)
# HARD_AVOIDANCE = config["hard_avoidance"]

# # Draw ONLY the agents, nothing else
# DRAW_AGENTS_ONLY = config["draw_agents_only"]

# # Show the chosen simulation without any colors or shader modifications
# DRAW_RAW = config["draw_raw"]

# # How fast the agent trails decay/dissapear per frame
# DECAY_RATE = config["decay_rate"] # 0-1

# # How much blur to apply to the agent trails per frame
# BLUR_RATE = config["blur_rate"] # 0-1

# # NOTE: I suggest you read the paper noted at the top of this file first before proceding

# # SLIME SPECIES (4 max)
# SPECIES = config["species"]
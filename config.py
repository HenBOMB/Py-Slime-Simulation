
# Slime Simulation Paper -> 
# https://uwe-repository.worktribe.com/output/980579

# Width and height of the screen and texture
WIDTH, HEIGHT = (512, 512)

# The amount of agents to simulate, must always be bigger than 16
AGENT_COUNT = 50000

# Instead of the above, use a percentage relative to the amount of pixels on the screen to determine the amount of agents
# PERCENT = 15
# AGENT_COUNT = math.floor(PERCENT / 100 * WIDTH * HEIGHT)

# How many times to compute the simulation per frame
STEPS_PER_FRAME = 5

# The postion the agents start the simulation in
# 0: random locations across the screen
# 1: all at the center
# 2: in a circle around the center with angle heading towards the center
STARTING_MODE = 0

# NOTE: I suggest you read the paper noted at the top of this file first before proceding

# forward left and forward right sensor angle from forward position
SA = 45 # degrees

# Agent rotation angle
RA = 45 # degrees

# Sensor offset distance
SO = 9 # px

# Step size — how far agent moves per step
SS = 1 # px

# Sensor width
SW = 1 # px

# some custom configs
# neurons?: SO=30; SS=3; SA/RA=5;
# dots: SW=10; SA/RA=90; SO=9

# How fast the agent trails decay/dissapear per frame
DECAY_RATE = 0.005 # 0-1

# How much blur to apply to the agent trails per frame
BLUR_RATE = 0.2 # 0-1

# Show the simulation without any colors or shader modifications
DRAW_RAW = False

# Draw ONLY the agents, nothing else
DRAW_ONLY_AGENTS = False

# Draw the simulation with a color
DRAW_COLOR = (.9, 0, .9, 1) # purple
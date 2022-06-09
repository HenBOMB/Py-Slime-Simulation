
# Slime Simulation Paper -> 
# https://uwe-repository.worktribe.com/output/980579

# Width and height of the screen and texture
WIDTH, HEIGHT = (1920 // 2, 1080 // 2)

# The amount of agents to simulate, must always be bigger than 16
AGENT_COUNT = 10000

# Instead of the above, use a percentage relative to the amount of pixels on the screen to determine the amount of agents
# PERCENT = 15
# AGENT_COUNT = math.floor(PERCENT / 100 * WIDTH * HEIGHT)

# How many times to compute the simulation per frame
STEPS_PER_FRAME = 1

# The postion the agents start the simulation in
# 0: random position and angle
# 1: all at the center with andom angle
# 2: random point in a circle with random mangle
# 3: random point in a circle with angle heading towards the center
# 4: random point in a circle rim with angle heading towards the center
STARTING_MODE = 1

# Make the agents die if they get trapped and cannot move or join another one of their species path
# Or if they collide with other species
DIE_ON_TRAPPED = False

# Does additional checks with the attempt of never colliding with other species (forces the agent to avoid other species as much as possible)
HARD_AVOIDANCE = False

# Draw ONLY the agents, nothing else
DRAW_AGENTS_ONLY = False

# Show the chosen simulation without any colors or shader modifications
DRAW_RAW = False

# How fast the agent trails decay/dissapear per frame
DECAY_RATE = 0.005 # 0-1

# How much blur to apply to the agent trails per frame
BLUR_RATE = 0.2 # 0-1

# NOTE: I suggest you read the paper noted at the top of this file first before proceding

# SLIME SPECIES (4 max)
SPECIES = [
    [
        # SA (0.0 - 360.0)  — Sendor Angle, forward left and forward right from forward position
        5,
        # RA (0.0 - 360.0)  — Rotation Angle
        5,
        # SO (px)           — Sensor Offset distance
        30,
        # SS (px)           — Step Size, how far agent moves per step
        1,
        # SW (px)           — Sensor Width (SW(1) = -1..1 = [-1, 0, 1], aka 3 width)
        1,
        # Color (0.0 - 1.0 or 0.0 - 255.0) — RGB
        (47, 45, 74)
    ], 
    [ 45, 45, 9, 1, 1, (140, 54, 57) ],
    [ 90, 45, 30, 1, 1, (24, 156, 243) ],
    # [ 45, 45, 30, 1, 1, (189, 209, 210) ],
]
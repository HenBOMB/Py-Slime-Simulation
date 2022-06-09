import math, glfw, random, struct, platform, time
import numpy as np

from compushady import config as _config
from compushady import HEAP_UPLOAD, HEAP_READBACK, Swapchain, Buffer, Texture2D, Compute
from compushady.formats import R16G16B16A16_FLOAT
from compushady.shaders import hlsl
from config import *

_config.set_debug(True)

AGENT_COUNT = (AGENT_COUNT // 32) * 32
HEIGHT = (HEIGHT // 32) * 32
WIDTH = (WIDTH // 32) * 32

#####################
# TEXTURE BUFFERS
#####################

trail_map = Texture2D(WIDTH, HEIGHT, R16G16B16A16_FLOAT)
diffused_trail_map = Texture2D(WIDTH, HEIGHT, R16G16B16A16_FLOAT)
display_texture = Texture2D(WIDTH, HEIGHT, R16G16B16A16_FLOAT)
display_agents_texture = Texture2D(WIDTH, HEIGHT, R16G16B16A16_FLOAT)
texture_staging_buffer = Buffer(trail_map.size, HEAP_UPLOAD)
texture_readback_buffer = Buffer(trail_map.size, HEAP_READBACK)

#####################
# SPECIES BUFFER
#####################

format = "fffffffffffff"
stride = struct.calcsize(format)
species_buffer = Buffer(stride * len(SPECIES), stride=stride, heap=HEAP_UPLOAD)

masks = [
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1],
]

data = b''.join([struct.pack(format, 
    *[
        math.radians(SPECIES[i][0]),
        math.radians(SPECIES[i][1]),
        SPECIES[i][2],
        SPECIES[i][3],
        SPECIES[i][4],
        SPECIES[i][5][0] / 255. if SPECIES[i][5][0] > 1 else SPECIES[i][5][0],
        SPECIES[i][5][1] / 255. if SPECIES[i][5][1] > 1 else SPECIES[i][5][1],
        SPECIES[i][5][2] / 255. if SPECIES[i][5][2] > 1 else SPECIES[i][5][2],
        1,
        *masks[i]
    ]) for i in range(len(SPECIES))]
)

species_buffer.upload(data)

#####################
# AGENT BUFFERS
#####################

# stride = the 'index' where the bytes will be sliced and used as buffer, an Agent struct in this case
format = "fffIf"
stride = struct.calcsize(format)

# unreadable and unwritable outside the compute shader, only used as storage
output_agents = Buffer(stride * AGENT_COUNT, stride=stride)
# the opposite i guess
readback_agents = Buffer(output_agents.size, HEAP_READBACK)
source_agents = Buffer(output_agents.size, stride=stride, heap=HEAP_UPLOAD)

if STARTING_MODE == 0:
    data = b''.join([struct.pack(format,
    *[
        random.random() * WIDTH,
        random.random() * HEIGHT,
        random.random() * 2. * math.pi,
        random.randint(0, len(SPECIES)-1),
        True
    ]) for _ in range(AGENT_COUNT)])

elif STARTING_MODE == 1:
    data = b''.join([struct.pack(format,
    *[
        WIDTH  / 2.,
        HEIGHT / 2.,
        random.random() * 2 * math.pi,
        random.randint(0, len(SPECIES)-1),
        True
    ]) for _ in range(AGENT_COUNT)])

elif STARTING_MODE == 2:
    def genData():
        theta = random.random() * 2. * math.pi
        radius = HEIGHT / 2. * random.random() - HEIGHT / 10
        return [
            WIDTH  / 2. + math.cos(theta) * radius, 
            HEIGHT / 2. + math.sin(theta) * radius, 
            theta,
            random.randint(0, len(SPECIES)-1),
            True
        ]
    data = b''.join([struct.pack(format, *genData()) for _ in range(AGENT_COUNT)])

elif STARTING_MODE == 3:
    def genData():
        theta = random.random() * 2. * math.pi
        radius = HEIGHT / 2. * random.random() - HEIGHT / 10
        pos = (
            WIDTH  / 2. + math.cos(theta) * radius, 
            HEIGHT / 2. + math.sin(theta) * radius
        )
        angle = math.atan2(
            (HEIGHT / 2. - pos[1]) / np.sqrt(np.sum((HEIGHT / 2. - pos[1])**2)),
            (WIDTH  / 2. - pos[0]) / np.sqrt(np.sum((WIDTH  / 2. - pos[0])**2))
        )
        return [
            pos[0], 
            pos[1], 
            angle,
            random.randint(0, len(SPECIES)-1),
            True
        ]
    data = b''.join([struct.pack(format, *genData()) for _ in range(AGENT_COUNT)])

else:
    def genData():
        theta = random.random() * 2. * math.pi
        radius = HEIGHT / 2. - HEIGHT / 10
        pos = (
            WIDTH  / 2. + math.cos(theta) * radius,
            HEIGHT / 2. + math.sin(theta) * radius
        )
        angle = math.atan2(
            (HEIGHT / 2. - pos[1]) / np.sqrt(np.sum((HEIGHT / 2. - pos[1])**2)),
            (WIDTH  / 2. - pos[0]) / np.sqrt(np.sum((WIDTH  / 2. - pos[0])**2))
        )
        return [
            pos[0], 
            pos[1], 
            angle, 
            random.randint(0, len(SPECIES)-1),
            True
        ]
    data = b''.join([struct.pack(format, *genData()) for _ in range(AGENT_COUNT)])

source_agents.upload(data)

#####################
# TIME BUFFER
#####################

time_staging_buffer = Buffer(8, HEAP_UPLOAD)
time_buffer = Buffer(time_staging_buffer.size, format=R16G16B16A16_FLOAT)

#####################
# SHADERS
#####################

# Passing every type of buffer into the shader
# https://github.com/rdeioris/compushady/blob/main/test/test_compute.py

# NOTE: Just wanted to keep the shader files as clean as possible
# Don't do this.. use a static buffer instead
def loadShader(name, srv, uav):
    s = open("shaders/{}.hlsl".format(name), "r").read()
    s = s.replace("!WIDTH", str(WIDTH)).replace("!HEIGHT", str(HEIGHT))
    s = s.replace("!BLUR_RATE", str(BLUR_RATE)).replace("!DECAY_RATE", str(DECAY_RATE))
    s = s.replace("!DRAW_AGENTS_ONLY", str(DRAW_AGENTS_ONLY).lower()).replace("!DRAW_RAW", str(DRAW_RAW).lower())
    s = s.replace("!DIE_ON_TRAPPED", str(DIE_ON_TRAPPED).lower())
    s = s.replace("!HARD_AVOIDANCE", str(HARD_AVOIDANCE).lower())
    s = s.replace("!NUM_SPECIES",  str(len(SPECIES)))
    s = s.replace("!NUM_AGENTS",  str(AGENT_COUNT))
    return Compute(hlsl.compile(s), [], srv, uav)

compute_agents = loadShader(
    "compute-agents",   [diffused_trail_map, source_agents, time_buffer, species_buffer], [diffused_trail_map, output_agents])
compute_trails = loadShader(
    "compute-trails",   [diffused_trail_map], [diffused_trail_map])
compute_agents_texture = loadShader(
    "color-agents",     [source_agents], [display_agents_texture])
compute_final_texture = loadShader(
    "color-screen",     [diffused_trail_map, species_buffer], [display_texture, display_agents_texture])

#####################
# WINDOW
#####################

time_start = time.time()

def computeSimulation():
    global time_start

    # Update the time buffer with a new time value
    time_staging_buffer.upload(struct.pack("f", time.time() - time_start))
    time_staging_buffer.copy_to(time_buffer)

    # Run the agents shader
    compute_agents.dispatch(AGENT_COUNT // 32, 1, 1)

    # Copy the output (output_agents) to a readback buffer and upload it to the input buffer (source_agents)
    output_agents.copy_to(readback_agents)
    source_agents.upload(readback_agents.readback())
        
    # Run the trails shader
    compute_trails.dispatch(WIDTH // 32, HEIGHT // 32, 1)

def computeDraw():
    if(DRAW_AGENTS_ONLY): compute_agents_texture.dispatch(WIDTH // 32, 1, 1)
    compute_final_texture.dispatch(WIDTH // 32, HEIGHT // 32, 1)

def main():
    glfw.init()
    glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

    window = glfw.create_window(WIDTH, HEIGHT, 'Slime Simulation', None, None)
    
    if platform.system() == 'Windows':
        swapchain = Swapchain(glfw.get_win32_window(window), R16G16B16A16_FLOAT, 3)
    else:
        swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), R16G16B16A16_FLOAT, 3)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        
        for _ in range(STEPS_PER_FRAME):
            computeSimulation()
            
        computeDraw()

        swapchain.present(display_texture)

    swapchain = None

    glfw.terminate()

if __name__ == "__main__":
    main()
import math, glfw, random, struct, platform, time
import numpy as np

from compushady import config as _config
from compushady import HEAP_UPLOAD, HEAP_READBACK, Swapchain, Buffer, Texture2D, Compute
from compushady.formats import R8G8B8A8_UNORM
from compushady.shaders import hlsl
from config import *

_config.set_debug(True)

# NOTE: Don't remove this
SA = math.radians(SA)
RA = math.radians(RA)

# region Core

#####################
# TEXTURE BUFFERS
#####################

trail_map = Texture2D(WIDTH, HEIGHT, R8G8B8A8_UNORM)
diffused_trail_map = Texture2D(WIDTH, HEIGHT, R8G8B8A8_UNORM)
display_texture = Texture2D(WIDTH, HEIGHT, R8G8B8A8_UNORM)
display_agents_texture = Texture2D(WIDTH, HEIGHT, R8G8B8A8_UNORM)
texture_staging_buffer = Buffer(trail_map.size, HEAP_UPLOAD)
texture_readback_buffer = Buffer(trail_map.size, HEAP_READBACK)

#####################
# AGENT BUFFERS
#####################

# stride = the 'index' where the bytearray will be sliced and used as buffer
# 12 bytes * the num of agents
# 12 bytes = float2 (8 bytes) + float (4 bytes)
stride = 12

# unreadable and unwritable outside the compute shader, only used as storage
output_agents = Buffer(stride * AGENT_COUNT, stride=stride)
# the opposite i guess
readback_agents = Buffer(output_agents.size, HEAP_READBACK)

source_agents = Buffer(output_agents.size, stride=stride, heap=HEAP_UPLOAD)
if STARTING_MODE == 0:
    data = b''.join(
        [struct.pack("fff", *[
            random.random() * WIDTH, 
            random.random() * HEIGHT, 
            random.random() * 2.0 * math.pi]) 
        for i in range(AGENT_COUNT)]
    )
elif STARTING_MODE == 1:
    data = b''.join(
        [struct.pack("fff", *[
            WIDTH  / 2., 
            HEIGHT / 2., 
            random.random() * 2.0 * math.pi])
        for i in range(AGENT_COUNT)]
    )
elif STARTING_MODE == 2:
    def gen_agent_on_circle(offset_radius):
        theta = random.random() * 2.0 * math.pi
        pos = (
            WIDTH  / 2. + math.cos(theta) * (WIDTH  / 2. - offset_radius),
            HEIGHT / 2. + math.sin(theta) * (HEIGHT / 2. - offset_radius)
        )
        angle = math.atan2(
            (HEIGHT / 2. - pos[1]) / np.sqrt(np.sum((HEIGHT / 2. - pos[1])**2)),
            (WIDTH  / 2. - pos[0]) / np.sqrt(np.sum((WIDTH  / 2. - pos[0])**2))
        )
        return [pos[0], pos[1], angle]
    data = b''.join([struct.pack("fff", *gen_agent_on_circle(HEIGHT // 10)) for i in range(AGENT_COUNT)])

source_agents.upload(data)

#####################
# TIME BUFFER
#####################

time_staging_buffer = Buffer(8, HEAP_UPLOAD)
time_buffer = Buffer(time_staging_buffer.size, format=R8G8B8A8_UNORM)

#####################
# SHADERS
#####################

# Passing every type of buffer into the shader
# https://github.com/rdeioris/compushady/blob/main/test/test_compute.py

# NOTE: Just wanted to keep the shader files as clean as possible
# Don't do this.. use a static buffer instead
def loadShader(path, srv, uav):
    s = open(path+ ".hlsl", "r").read()
    s = s.replace("!WIDTH", str(WIDTH)).replace("!HEIGHT", str(HEIGHT))
    s = s.replace("!SA", str(SA)).replace("!RA", str(RA))
    s = s.replace("!SO", str(SO)).replace("!SS", str(SS)).replace("!SW", str(SW))
    s = s.replace("!BLUR_RATE", str(BLUR_RATE)).replace("!DECAY_RATE", str(DECAY_RATE))
    s = s.replace("!DRAW_ONLY_AGENTS", str(DRAW_ONLY_AGENTS).lower()).replace("!DRAW_RAW", str(DRAW_RAW).lower())
    s = s.replace("!DRAW_COLOR", "float4" + str(DRAW_COLOR))
    return Compute(hlsl.compile(s), [], srv, uav)

compute_agents = loadShader(
    "compute-agents",   [trail_map, source_agents, time_buffer],    [diffused_trail_map, output_agents])
compute_trails = loadShader(
    "compute-trails",   [diffused_trail_map],                       [diffused_trail_map])
compute_agents_texture = loadShader(
    "color-agents",     [source_agents],                            [display_agents_texture])
compute_final_texture = loadShader(
    "color-screen",     [trail_map, display_agents_texture],        [display_texture, display_agents_texture])

#####################
# WINDOW
#####################

time_start = time.time()

def computeSimulation():
    global time_start

    if time.time() - time_start > 5:
        time_start = time.time()

    # Update the time buffer with a new time value
    time_staging_buffer.upload(struct.pack("f", time.time() - time_start))
    time_staging_buffer.copy_to(time_buffer)

    # Run the agents shader
    compute_agents.dispatch(AGENT_COUNT // 16, 1, 1)

    # Copy the output (output_agents) to a readback buffer and upload it to the input buffer (source_agents)
    output_agents.copy_to(readback_agents)
    source_agents.upload(readback_agents.readback())
        
    # Run the trails diffuse/blur shader
    compute_trails.dispatch(WIDTH // 8, HEIGHT // 8, 1)

    # Copy the output (diffused_trail_map) to a readback buffer and upload it to the input buffer (trail_map)
    diffused_trail_map.copy_to(texture_readback_buffer)
    texture_staging_buffer.upload(texture_readback_buffer.readback())
    texture_staging_buffer.copy_to(trail_map)

def computeDraw():
    if(DRAW_ONLY_AGENTS):
        compute_agents_texture.dispatch(WIDTH // 16, 1, 1)
    compute_final_texture.dispatch(WIDTH // 8, HEIGHT // 8, 1)

def main():
    glfw.init()
    glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

    window = glfw.create_window(WIDTH, HEIGHT, 'Slime Simulation', None, None)
    
    if platform.system() == 'Windows':
        swapchain = Swapchain(glfw.get_win32_window(window), R8G8B8A8_UNORM, 3)
    else:
        swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), R8G8B8A8_UNORM, 3)

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

#endregion
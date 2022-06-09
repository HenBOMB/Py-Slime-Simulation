import math, glfw, random, struct, platform, time, json
import numpy as np
from PIL import Image

from compushady import HEAP_UPLOAD, HEAP_READBACK, Swapchain, Buffer, Texture2D, Compute
from compushady.formats import R16G16B16A16_FLOAT, R8G8B8A8_UNORM
from compushady.shaders import hlsl

ENCODING_FORMAT = R16G16B16A16_FLOAT
AGENT_THREADS = 32
TEXTURE_THREADS = 32

# Draw only the agents on the screen
DRAW_AGENTS_ONLY = False

# Draw a faint glow of where the food are
DRAW_FOOD = False

#TODO: Not working with format 'R16G16B16A16_FLOAT', use 'R8G8B8A8_UNORM' when recording.
recording_frames = 0
recording_images = []
recording_path = ""

FOOD = []

def setFood(position, radius, weight):
    FOOD.append(struct.pack("IIff", *[
        int(position[0]),
        int(position[1]),
        radius,
        weight
    ]))

def run(path):
    config = json.load(open(path))
    defaults = json.load(open("configs/defaults.json"))
    global recording_frames
    global recording_images
    global recording_path

    #####################
    # INIT
    #####################

    def getProperty(name):
        return config[name] if name in config else defaults[name]

    WIDTH               = getProperty("width")
    HEIGHT              = getProperty("height")
    AGENT_COUNT         = getProperty("agent_count")
    STEPS_PER_FRAME     = getProperty("steps_per_frame")
    SPAWN_MODE          = getProperty("spawn_mode")
    HARD_AVOIDANCE      = getProperty("hard_avoidance")
    DECAY_RATE          = getProperty("decay_rate")
    BLUR_RATE           = getProperty("blur_rate")
    SPECIES             = getProperty("species")
    AGENT_OVERLAPPING   = getProperty("agent_overlapping")
    RADIAL_BOUNDARY     = getProperty("radial_boundary")
    BORDER              = getProperty("border")
    
    HEIGHT = (HEIGHT // TEXTURE_THREADS) * TEXTURE_THREADS
    WIDTH = (WIDTH // TEXTURE_THREADS) * TEXTURE_THREADS

    AGENT_COUNT = (AGENT_COUNT // AGENT_THREADS) * AGENT_THREADS

    #####################
    # TEXTURE BUFFERS
    #####################

    display_texture = Texture2D(WIDTH, HEIGHT, ENCODING_FORMAT)
    blur_texture = Texture2D(WIDTH, HEIGHT, ENCODING_FORMAT)
    diffused_trail_map = Texture2D(WIDTH, HEIGHT, ENCODING_FORMAT)
    agents_texture = Texture2D(WIDTH, HEIGHT, ENCODING_FORMAT)
    record_buffer = Buffer(display_texture.size, HEAP_READBACK)

    bff = Buffer(display_texture.size, HEAP_UPLOAD)
    bff.upload(bytes([random.randint(0, 255), random.randint(
        0, 255), random.randint(0, 255), 255]) * (display_texture.size // 4))
    bff.copy_to(display_texture)

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
    # FOOD BUFFER
    #####################

    format = "IIff"
    stride = struct.calcsize(format)
    food_buffer = Buffer(stride * len(FOOD), stride=stride, heap=HEAP_UPLOAD)
    food_buffer.upload(b''.join(FOOD))

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

    def generateAgentsData():
        if SPAWN_MODE == 0:
            data = b''.join([struct.pack(format,
            *[
                random.random() * WIDTH,
                random.random() * HEIGHT,
                random.random() * 2. * math.pi,
                random.randint(0, len(SPECIES)-1),
                True
            ]) for _ in range(AGENT_COUNT)])

        elif SPAWN_MODE == 1:
            data = b''.join([struct.pack(format,
            *[
                WIDTH  / 2.,
                HEIGHT / 2.,
                random.random() * 2 * math.pi,
                random.randint(0, len(SPECIES)-1),
                True
            ]) for _ in range(AGENT_COUNT)])

        elif SPAWN_MODE == 2:
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

        elif SPAWN_MODE == 3:
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

    generateAgentsData()

    #####################
    # TIME BUFFER
    #####################

    time_buffer = Buffer(4, stride=4, heap=HEAP_UPLOAD)

    #####################
    # SHADERS
    #####################

    # Passing every type of buffer into the shader
    # https://github.com/rdeioris/compushady/blob/main/test/test_compute.py

    # NOTE: Just wanted to keep the shader files as clean as possible
    # Don't do this.. use a static buffer instead
    def loadShader(name, srv, uav):
        s = open("shaders/{}.hlsl".format(name), "r").read()
        s = s.replace("!WIDTH",             str(WIDTH))
        s = s.replace("!HEIGHT",            str(HEIGHT))
        s = s.replace("!BLUR_RATE",         str(BLUR_RATE))
        s = s.replace("!DECAY_RATE",        str(DECAY_RATE))
        s = s.replace("!DRAW_AGENTS_ONLY",  str(DRAW_AGENTS_ONLY).lower())
        s = s.replace("!RADIAL_BOUNDARY", str(RADIAL_BOUNDARY).lower())
        s = s.replace("!DRAW_FOOD",         str(DRAW_FOOD).lower())
        s = s.replace("!HARD_AVOIDANCE",    str(HARD_AVOIDANCE).lower())
        s = s.replace("!AGENT_OVERLAPPING", str(AGENT_OVERLAPPING).lower())
        s = s.replace("!NUM_AGENTS",        str(AGENT_COUNT))
        s = s.replace("!NUM_SPECIES",       str(len(SPECIES)))
        s = s.replace("!NUM_FOOD",          str(len(FOOD)))
        s = s.replace("!AGENT_THREADS",     str(AGENT_THREADS))
        s = s.replace("!TEXTURE_THREADS",   str(TEXTURE_THREADS))
        s = s.replace("!BORDER",            str(BORDER))
        return Compute(hlsl.compile(s), [], srv, uav)

    compute_agents = loadShader(
        "compute-agents",   [diffused_trail_map, source_agents, time_buffer, species_buffer, food_buffer, agents_texture],
                            [diffused_trail_map, output_agents, agents_texture])
    compute_trails = loadShader(
        "compute-trails",   [diffused_trail_map], 
                            [diffused_trail_map])
    compute_agents_texture = loadShader(
        "color-agents",     [source_agents], 
                            [agents_texture])
    compute_display_texture = loadShader(
        "color-screen",     [diffused_trail_map, agents_texture, species_buffer, blur_texture, food_buffer], 
                            [display_texture, agents_texture])

    compute_blur_shader = loadShader("blur", [blur_texture], [blur_texture])

    #####################
    # WINDOW
    #####################

    time_start = time.time()

    def computeSimulation():

        # Update the time buffer with a new time value
        time_buffer.upload(struct.pack("f", time.time() - time_start))

        # Run the agents shader
        compute_agents.dispatch(AGENT_COUNT // AGENT_THREADS, 1, 1)

        # Copy the output (output_agents) to a readback buffer and upload it to the input buffer (source_agents)
        output_agents.copy_to(readback_agents)
        source_agents.upload(readback_agents.readback())
            
        # Run the trails shader
        compute_trails.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)

    def computeDraw():
        if(DRAW_AGENTS_ONLY): 
            compute_agents_texture.dispatch(AGENT_COUNT // AGENT_THREADS, 1, 1)
            # clear the texture
            Buffer(display_texture.size, HEAP_UPLOAD).copy_to(blur_texture)
            compute_display_texture.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)
            return

        # clear the texture
        Buffer(display_texture.size, HEAP_UPLOAD).copy_to(blur_texture)

        compute_display_texture.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)

        display_texture.copy_to(blur_texture)
        
        compute_blur_shader.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)
        compute_blur_shader.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)
        compute_blur_shader.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)
        compute_blur_shader.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)

        compute_display_texture.dispatch(WIDTH // TEXTURE_THREADS, HEIGHT // TEXTURE_THREADS, 1)
        
    glfw.init()
    glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

    window = glfw.create_window(WIDTH, HEIGHT, 'Slime Simulation', None, None)
        
    if platform.system() == 'Windows':
        swapchain = Swapchain(glfw.get_win32_window(window), ENCODING_FORMAT, 3)
    else:
        swapchain = Swapchain((glfw.get_x11_display(), glfw.get_x11_window(window)), ENCODING_FORMAT, 3)

    while not glfw.window_should_close(window):
        glfw.poll_events()

        if glfw.get_key(window, glfw.KEY_R):
            generateAgentsData()
            Buffer(display_texture.size, HEAP_UPLOAD).copy_to(diffused_trail_map)
            continue

        for _ in range(STEPS_PER_FRAME):
            computeSimulation()
                
        computeDraw()

        if(recording_frames > 0):
            display_texture.copy_to(record_buffer)
            image = Image.new('RGBA', (WIDTH, HEIGHT))
            image.frombytes(record_buffer.readback())
            recording_images.append(image)
            recording_frames -= 1
            print("frame: {}".format(recording_frames))
        elif(len(recording_images) > 0):
            recording_images[0].save(recording_path, save_all=True, append_images=recording_images[1:], duration=150, loop=0)
            recording_images = []

        swapchain.present(display_texture)

    swapchain = None

    glfw.terminate()

# not working
def record(frames, path = "recording.gif"):
    global recording_frames
    global recording_images
    global recording_path

    recording_images = []
    recording_frames = frames + 1
    recording_path = path
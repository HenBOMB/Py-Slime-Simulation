import simulation

O_WIDTH = 500
O_HEIGHT = 500

def main():
    # simulation.run("")
    # simulation.record(30)
    simulation.setFood((O_WIDTH / 2 - O_HEIGHT / 4, O_HEIGHT / 2), 15, 1)
    simulation.setFood((O_WIDTH / 2 + O_HEIGHT / 4, O_HEIGHT / 2), 15, 1)
    simulation.run("configs/a8.json", O_WIDTH, O_HEIGHT)

if __name__ == "__main__":
    main()
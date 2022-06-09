import simulation

O_WIDTH = 500
O_HEIGHT = 500

def main():
    simulation.setFood((O_WIDTH / 2 - O_HEIGHT / 4, O_HEIGHT / 2), 7, .4)
    simulation.setFood((O_WIDTH / 2 + O_HEIGHT / 4, O_HEIGHT / 2), 7, .4)
    simulation.run("configs/food.json", O_WIDTH, O_HEIGHT)

if __name__ == "__main__":
    main()
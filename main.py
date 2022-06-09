import simulation

def main():
    simulation.setFood((50, 100), 7, .4)
    simulation.setFood((150, 100), 7, .4)
    simulation.run("configs/food.json")

if __name__ == "__main__":
    main()
# Python Slime-Simulation

Simple python pogram based on this [slime simulation paper](https://uwe-repository.worktribe.com/output/980579), using compute shaders to run the simulation.

##  Default Configuration

```json
{
    "width":            960,
    "height":           540,
    "agent_count" :     10000,
    "steps_per_frame":  1,
    "starting_mode":    1,
    "die_on_trapped":   false,
    "death_time":       20,
    "hard_avoidance":   false,
    "draw_agents_only": false,
    "decay_rate":       0.01,
    "blur_rate":        0.2,
    "species":          [
        [ 22.5, 45, 9, 1, 1, [1, 1, 1] ]
    ]
}
```

### What each property does

**`agent_count`**
The amount of agents to run in the simulation.

**`steps_per_frame`**
The amount of updates to run per frame (fps auto-capped at 60)

**`starting_mode`**
The starting positions of the agents.
Could be either of the following:
> `0` Random position and angle.<br>
<br>> `1` All at the center with a random angle.
<br>> `2` Random point in a circle with random angle.
<br>> `3` Random point in a circle with angle towards the center.
<br>> `4` R andom point in a circle rim with angle towards the center.

**```die_on_trapped```**
The agents will die if they get surrounded by other species agents, cannot move, join another one of their species path or if they collide with other species.

**`death_time`**
Agents will start dying after `death_time` seconds, this is to give them some time to spread out when spawned, since many will spawn on top of each other.

**`hard_avoidance`**
Does additional checks with the attempt of forcing the agent to avoid other species as much as possible.

**`draw_agents_only`**
Draw only the agents on the screen.

**`decay_rate`**
How fast the agent trails decay/dissapear per frame.

**`blur_rate`**
How much blur to apply to the agent trails per frame.

**`species`**
<br>**`0`** SA: FL and FR sensor angle from forward position
<br>**`1`** RA: Agent rotation angle
<br>**`2`** SO: Sensor offset distance
<br>**`3`** SW: Sensor width
<br>**`4`** SS: Step size—how far agent moves per step
<br>**`5`** Color: The color of the species in RGB

*Used [compushady](https://github.com/rdeioris/compushady) to run the `HLSL` compute shaders.*
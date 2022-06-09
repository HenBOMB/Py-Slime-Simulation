# Python Slime-Simulation

Simple python pogram based on this [slime simulation paper](https://uwe-repository.worktribe.com/output/980579), using compute shaders to run the simulation.

##  Default Configuration

```json
{
    "width" :           930,
    "height":           540,
    "agent_count" :     10000,
    "steps_per_frame":  1,
    "spawn_mode":       1,
    "die_on_trapped":   false,
    "death_time":       20,
    "hard_avoidance":   false,
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

**`spawn_mode`**
How the agents spawn when starting the simulation.
Could be either of the following:
<br>`0` Random position and angle.
<br>`1` All at the center with a random angle.
<br>`2` Random point in a circle with random angle.
<br>`3` Random point in a circle with angle towards the center.
<br>`4` R andom point in a circle rim with angle towards the center.

**```die_on_trapped```**
Make the agents die if they get surrounded, cannot move, or collide with other species.

**`death_time`**
Agents will start dying after `death_time` seconds, this is to give them time to spread out when spawned, since many will spawn on top of each other.

**`hard_avoidance`**
Does additional checks to minimize the chance of colliding with other species.

**`decay_rate`**
How much to decay the agent trails per frame.

**`blur_rate`**
How much to blur the agent trails per frame.

**`species`** Array containing all the spieces to simulate. **`(max 4)`**
<br>**`[0]`** SA: FL and FR sensor angle from forward position. `deg`
<br>**`[1]`** RA: Agent rotation angle. `deg`
<br>**`[2]`** SO: Sensor offset distance. `px`
<br>**`[4]`** SS: Step size, how far agent moves per step. `px`
<br>**`[3]`** SW: Sensor width. `px`
<br>**`[5]`** Color: The color of the species in `RGB 0-1 or 0-255`.

## Examples

`a5.json`<br>
![2022-06-09-04-38-03](https://user-images.githubusercontent.com/58308591/172794499-1cbbc49c-2f35-4570-940f-1f060e566d5f.gif)

`a2.json`<br>
![2022-06-09-04-57-12](https://user-images.githubusercontent.com/58308591/172796142-fa582528-5d6b-4962-b4a3-a67c3f8a3888.gif)

`a6.json`<br>
![2022-06-09-05-12-03](https://user-images.githubusercontent.com/58308591/172798796-e7cdc10f-5239-4127-be08-02e399d6c2a7.gif)

***Used [compushady](https://github.com/rdeioris/compushady) to run the `HLSL` compute shaders.***

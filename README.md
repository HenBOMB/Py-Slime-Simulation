# Python Slime-Simulation
Simple artificial life python program based on this [slime simulation paper](https://uwe-repository.worktribe.com/output/980579), using compute shaders to run the simulation.

*"Characteristics of Pattern Formation and Evolution in Approximations of Physarum Transport Networks"*

![preview](https://user-images.githubusercontent.com/58308591/172806152-beb0f50a-022d-442f-a754-de3de231ed75.png)

##  Default Configuration

```json
{
    "width" :           930,
    "height":           540,
    "agent_count":      10000,
    "steps_per_frame":  1,
    "spawn_mode":       1,
    "agent_overlapping":true,
    "radial_boundary":  false,
    "border":           0,
    "decay_rate":       0.01,
    "blur_rate":        0.2,
    "species": [
        [ 22.5, 45, 9, 1, 1, [1, 1, 1] ]
    ]
}
```

### What each property does

* ```agent_count```: The amount of agents to run in the simulation
* ```steps_per_frame```: The amount of updates to run per frame (fps auto-capped at 60)
* ```spawn_mode```: How the agents spawn when starting the simulation
<br>**0**: Random position and angle
<br>**1**: All at the center with a random angle
<br>**2**: Random point in a circle with random angle
<br>**3**: Random point in a circle with angle towards the center
<br>**4**: Random point in a circle rim with angle towards the center
* ```agent_overlapping```: When false, agents cannot move to a cell where another agent already is
* ```radial_boundary```: Sets the agents boundary to a circle `(height/2)`
* ```border```: Border boundary offset
* ```decay_rate```: How much to decay the agent trails per frame
* ```blur_rate```: How much to blur the agent trails per frame
* ```species```:  Array containing all the spieces to simulate. **`(max 4)`**
<br>**[0]** SA: FL and FR sensor angle from forward position. `deg`
<br>**[1]** RA: Agent rotation angle. `deg`
<br>**[2]** SO: Sensor offset distance. `px`
<br>**[4]** SS: Step size, how far agent moves per step. `px`
<br>**[3]** SW: Sensor width. `px`
<br>**[5]** Color: The color of the species in `RGB 0-1 or 0-255`.

## Examples

`a5.json`<br>
![2022-06-09-04-38-03](https://user-images.githubusercontent.com/58308591/172794499-1cbbc49c-2f35-4570-940f-1f060e566d5f.gif)

`a2.json`<br>
![2022-06-09-05-16-54](https://user-images.githubusercontent.com/58308591/172800295-90a3ef2c-a468-4e06-91fd-d53df27eb294.gif)

`a6.json`<br>
![2022-06-09-05-12-03](https://user-images.githubusercontent.com/58308591/172798796-e7cdc10f-5239-4127-be08-02e399d6c2a7.gif)

`food.json`, 200 agents find the shortest path between two food sources. (sped up by 300x)<br>
![2022-06-09-16-21-18](https://user-images.githubusercontent.com/58308591/172929483-0d46261a-ebdf-4a59-adfb-1087ef2919a4.gif)

***Used [compushady](https://github.com/rdeioris/compushady) to run the `HLSL` compute shaders.***

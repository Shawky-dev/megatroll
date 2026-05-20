# setup:
1. export the assets/models path to gz sim 
`export GZ_SIM_RESOURCE_PATH=~/.gz/sim/models`

0. in the megajaw.xacro.urdf manually switch depending on simulation or real life (todo make it auto switch)
0.1. in index.js change the connection port depending on if real life or simulation (todo change this too so it changes dynamically)
1. run simulation: ros2 launch megajaw_bringup gz.launch.py
2. run the web_interface/index.html
3. start recording: ros2 bag record /camera/image/compressed

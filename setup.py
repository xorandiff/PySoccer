import cx_Freeze

executables = [cx_Freeze.Executable('game.py', base = "Win32GUI")]

cx_Freeze.setup(
    name = "PySoccer",
    options = {"pysoccer_exe" : 
        {"packages" : ["pygame", "pymunk", "twisted"], "include_files" : ['img/ball.png', 'img/field.jpg', 'img/goal_post.png', 'img/grass.jpg', 'img/player.png', 'sound/kick.mp3', 'sound/post_hit.mp3']}},
    executables = executables
)
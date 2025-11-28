& {
    $repoRoot = $(git rev-parse --show-toplevel) -replace "/", "\"

    # Defaults only configuration
    python $repoRoot\local\local_render\local_render.py -d -t 19:34 --publish
    Copy-Item $repoRoot\local\local_render\local_render.png $repoRoot\docs\assets\defaults-only.png

    # Old defaults only configuration
    python $repoRoot\local\local_render\local_render.py -o -t 19:34 --publish
    Copy-Item $repoRoot\local\local_render\local_render.png $repoRoot\docs\assets\old-defaults.png

    # Wear OS configuration
    python $repoRoot\local\local_render\local_render.py -w -t 19:34 --publish
    Copy-Item $repoRoot\local\local_render\local_render.png $repoRoot\docs\assets\wearos-config.png

    # Random light configuration
    python $repoRoot\local\local_render\local_render.py -r -t 19:34 --publish --custom-theme '{"avgline_style": "-."}'
    Copy-Item $repoRoot\local\local_render\local_render.png $repoRoot\docs\assets\random-light.png
}

# First physical prototype — current direction

> Earlier study: the current A0 geometry, parts and release holds are in [engineering-report.md](engineering-report.md). Use that report for fabrication planning.


The current design is **25× terrain and a 50-mile visit radius**. Read [the detailed build guide](build-guide.md), also available at https://trentconley.github.io/globe/build-guide.html.

The earlier 72-LED strip test has been superseded as the main prototype because its spacing cannot adequately sample a 3.85 mm-wide footprint. The recommended first optical bench uses the identified Adafruit 5201 3 mm-pitch matrix, Adafruit 5426 controller and Adafruit 757 voltage shifter, with carefully separated USB and LED power positives and a common ground.

The engineering folder contains four thickness coupons, three small curved samples (smooth, Vancouver and Himalayas), the footprint command pattern, calculations, a BOM and a test log. Use the small samples before ordering a complete shell. The full-size approximately 95 mm section remains a geometry/finish study; its blank carrier is a legacy strip fixture, not the mounting design for the dense matrix.

Review print units, material, supports, wiring, current limiting and the optical acceptance targets in the guide. The sample meshes are checked; their physical printing, transmission and temperature behavior are not established. The bench code is supplied as an untested starting utility, not the final Wi-Fi device firmware.

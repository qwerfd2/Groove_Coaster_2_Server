The 2 platform uses BGM + SHOT, but mobile uses BGM or SHOT.
This requires reprocessing the SHOT audio.
Layering the audios directly (in audition, for example) won't work because the volume won't be preserved due to potential overflow of int16.
This script preserves the volume by calculating things in int32 before capping everything back, ensuring that the audio volume stays consistent.
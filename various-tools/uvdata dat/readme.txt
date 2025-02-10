uvdata is like the plist for the sprite sheets. To edit their dimensions, this tool can be used.

Parse uvdata.dat to uvdata.xlsx, and write it back to out_uvdata.dat.

Each row of uvdata is the dimension of that image.bin. 8 byte of header is included (file index, number of elements)

Use the encode/decode.py to convert the header-removed hex strings to/from json coordinates.
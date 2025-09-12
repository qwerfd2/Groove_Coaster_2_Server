# server_checker

This is a flutter app for batch downloading GC2OS server assets (music and charts) to the user's device (their application folder).

To use it, you need to

1) Compile the project to .apk or .ipa,

2) Sign the package to match the game client exactly (so you can install/sideload them and have them share the resource folders),

3) Install the package,

4) Generate a `batch_token` in the database through some means (database edit, discord bot, etc.)

5) Open the app and enter the server base URL and token,

6) Click download and wait!

This is a beta solution. Please report issues and errors.

Discord bot will not be open-sourced at the time being due to security concerns.

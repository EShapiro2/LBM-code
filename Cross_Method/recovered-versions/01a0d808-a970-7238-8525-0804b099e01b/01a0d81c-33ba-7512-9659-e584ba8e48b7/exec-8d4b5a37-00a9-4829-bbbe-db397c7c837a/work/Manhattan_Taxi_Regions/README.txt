MANHATTAN TAXI REGIONS - how to open
====================================

This folder holds one interactive web page: Manhattan_Taxi_Regions.html
It runs entirely in your web browser. Nothing to install, no internet needed
(only the fonts load from the internet; without it the page still works).

HOW TO OPEN
-----------
1. Unzip first. Right-click the .zip file and choose "Extract All..."
   (on a Mac, double-click the .zip). Opening the page from inside the zip
   often does not work.
2. Double-click Manhattan_Taxi_Regions.html. It opens in your web browser.
   Chrome, Edge, Firefox and Safari all work.
3. If it opens in a text editor or shows code instead of a page:
   right-click the file > "Open with" > choose Chrome or Edge.

IF WINDOWS BLOCKS IT
--------------------
Files downloaded from email or the web are sometimes marked as blocked.
Right-click Manhattan_Taxi_Regions.html > Properties > tick "Unblock"
at the bottom of the General tab > OK. Then double-click it again.

WHAT YOU WILL SEE
-----------------
24,101 real yellow-taxi pickups in Manhattan (15 January 2015, 8-9 am),
divided into regions in two different ways. Three tabs at the top:

  K-means with merging  Splits Manhattan until every region holds at most
                        T pickups, then merges neighbouring regions up to T'.
  Hexagon               A honeycomb of K hexagons whose corners move toward
                        balance for a chosen number of rounds.
  Compare               Both methods on the same pickups, side by side,
                        with a table of which one does better.

Use the sliders on the right to change the parameters; Play / Run starts
and stops each simulation.

USING CLAUDE TO OPEN IT
-----------------------
If you use Claude Code, open this folder with it and say:
    "open the page"
The file CLAUDE.md here tells Claude what to do.

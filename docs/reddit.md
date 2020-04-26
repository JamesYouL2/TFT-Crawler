TFTSheet is another statistics based TFT tier list like kda.gg and metatft.com. This is based off data from challengers for the past 2 days through the riotgames api.

(sheet)[]

Here are pros and cons of my project.
Pros:
1. This tier list will keep similar comps together. I think kda.gg and metatft.com split up comps too aggressively. 
There are definitely comps on these sites which should be together but are not. 
I am doing the opposite. There are not going to be comps on this sheet that should be clustered together but are not.
Basically, I'm not going to show 15+ comps on this tier list. I should only be showing 4-6, depending on the galaxy. 
There are going to be comps that are clustered together and should not be. I think HDBScan is putting together Blademaster comps and Cybernetics comps.
But that's the trade off I am accepting in exchange making sure that the comps that this algorithm finds are accurately rated.

2. It's open source. If you have the skills and drive, you can use this project to download your own data and run your own analysis on it. And if you have an improvement on my pretty noobish code, go for it.

3. Like metatft.com, I am splitting up the data by galaxy before clustering. This data shows there are significant differences across galaxies. Cybernetics is not a great comp normally, but in both Neeko and Rank5FoN universes, it's a great one.

Cons:
1. I do not have access to in-round data. I am only looking at endgame comps. Without partnering with a website that has an app that tracks games, data cannot tell you how to position or transition or level up. 
All this data tells you is that certain comps are good and that certain comps might be overrrated.

2. You are not going to find every relevant comp in the game. I don't show Star Guardian Sorcerers after the nerf or Protector comps. Also note that I am not clustering every comp and I am not showing those comps.

3. I don't know javascript and have almost zero front end skills. This is just not going to look as good as kda.gg or metatft.com.

Thanks for reading, please give me feedback and even better, make some pull requests.
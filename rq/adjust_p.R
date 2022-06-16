args <- commandArgs(trailingOnly = TRUE)
root = args[1]
from = args[2]
data <- read.csv(paste(root, from, sep="/"), sep=",")
adjusted_p = p.adjust(data[["p"]], method = "BH", n = length(data[["p"]]))
sink(paste(root, "adjusted_p.txt", sep="/"))
cat(adjusted_p)
sink()
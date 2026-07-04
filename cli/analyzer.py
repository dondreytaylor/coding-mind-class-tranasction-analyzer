import csv
import json
import matplotlib.pyplot as plt

dates = []
categories = []
descriptions = []
amounts = []

file = open("transactions.csv", "r")
reader = csv.reader(file)
next(reader)
for row in reader:
    dates.append(row[0])
    categories.append(row[1])
    descriptions.append(row[2])
    amounts.append(float(row[3]))
file.close()

data = []
for i in range(len(dates)):
    data.append({"date": dates[i], "category": categories[i], "description": descriptions[i], "amount": amounts[i]})
file = open("output.json", "w")
json.dump(data, file, indent=2)
file.close()

file = open("output.csv", "w", newline="")
writer = csv.writer(file)
writer.writerow(["date", "category", "description", "amount"])
for i in range(len(dates)):
    writer.writerow([dates[i], categories[i], descriptions[i], amounts[i]])
file.close()

category_totals = {}
for i in range(len(categories)):
    cat = categories[i]
    if cat in category_totals:
        category_totals[cat] = category_totals[cat] + amounts[i]
    else:
        category_totals[cat] = amounts[i]

plt.figure()
plt.pie(category_totals.values(), labels=category_totals.keys(), autopct="%1.1f%%")
plt.savefig("pie.png")

plt.figure()
plt.bar(category_totals.keys(), category_totals.values())
plt.savefig("bar.png")

total = 0
for amount in amounts:
    total = total + amount
print("Total spending: $" + str(round(total, 2)))

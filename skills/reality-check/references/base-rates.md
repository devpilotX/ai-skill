# Base rates

Where to retrieve business survival data, and how to read it. This file stores no numbers on purpose.
Survival rates change with every release and differ by country, sector and definition, so retrieve the
current table and cite it.

## Where to look

United States. The Bureau of Labor Statistics Business Employment Dynamics programme publishes
[establishment age and survival data](https://www.bls.gov/bed/bdmage.htm): tables that follow each annual
cohort of new private sector establishments and report how many are still operating each later year, with
breakdowns by industry sector. It covers establishments with employees, so sole traders with no payroll
are outside it. The US Census Bureau's Business Dynamics Statistics is a second source built from
different records; name it if the two disagree.

United Kingdom. The Office for National Statistics publishes the annual Business demography, UK bulletin
with its dataset tables, which report births, deaths, and one to five year survival of each birth cohort,
by industry and region. It counts businesses on the Inter-Departmental Business Register, meaning those
registered for VAT or PAYE, so very small unregistered businesses are missing.

European Union. Eurostat publishes business demography statistics for member states, including survival
rates of enterprises by age, sector and country. Start from the
[Business demography statistics](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Business_demography_statistics)
article and follow it to the data tables. Coverage and thresholds differ by country, so read the metadata
before comparing two countries.

Elsewhere. Look for the national statistics office's business demography or enterprise survival
release. If none exists, say so and treat the base rate as unknown rather than borrowing another
country's figure without saying so.

## How to read a cohort survival table

A cohort is every business born in the same year. The table shows what share of that cohort still
operates one, two, three and more years later. Read down a single cohort, not across different cohorts,
because each row started in a different economy.

Check the unit. An establishment is one location, a firm or enterprise can own many, and the two survive
at different rates. A franchise outlet closing can be an establishment death inside a surviving firm.

Check what counts as a death. Most sources count a business that stops trading or leaves the register.
A business that is sold, merges, or changes legal form may appear as a death in one source and a survivor
in another. None of them distinguishes a planned closure from a failure.

Check the sector granularity. A published sector such as "retail trade" or "construction" averages very
different businesses. Use the finest sector the source offers and say how close it is to the user's
category.

Use the latest cohort old enough to answer the question. Five year survival needs a cohort born at least
five years before the last data year, so the figure always describes an older economy.

State the survival figure as the base rate for an average entrant, then ask what this user has that the
average entrant did not. The base rate is the starting point for the verdict, not the verdict.

## Categories the tables do not cover well

Side projects, freelancers without payroll, and unregistered businesses, which fall below the thresholds
of most registers.

Online-only products and apps, which sit inside broad software or information sectors.

New categories without enough cohorts yet, such as model-wrapper products.

For these, say the base rate is not published, give the nearest sector figure with that caveat, and move
the weight of the verdict onto the load-bearing assumption and the seven-day test.

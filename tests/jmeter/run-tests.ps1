##############################################################################################
# -n = Non-GUI mode
# -t = testplan
# -l = reports
# -e = generate a visual report
# -o = output folder of html
# -f = override previous report(not working)
##############################################################################################
jmeter -n -t test-plans/classify_dogs_cats_test.jmx -l reports/results.jtl -e -o reports/html-report


test-case-1
	throughput_udp_iperf_h1-h4.txt
		h1> iperf -c 10.0.5.2 -u -b 28M | tee measurements/test-case-1/t
		h4> iperf -s -u
	throughput_udp_iperf_h1-h9.txt
		h1> iperf -c 10.0.7.2 -u -b 20M | tee measurements/test-case-1/
		h9> iperf -s -u
	throughput_udp_iperf_h7-h9.txt
		h7> iperf -c 10.0.7.2 -u -b 20M | tee measurements/test-case-1/
		h9> iperf -s -u

test-case-2
	latency_L1.txt
		mininet> r1 ping r2 -c 25 | tee measurements/test-case-2/latency_L1.txt
	latency_L2.txt
		mininet> r2 ping r3 -c 25 | tee measurements/test-case-2/latency_L2.txt
	latency_L3.txt
		mininet> r3 ping r4 -c 25 | tee measurements/test-case-2/latency_L3.txt


test-case-3
	latency_h1-h4.txt
		mininet> h1 ping h4 -c 25
	latency_h1-h9.txt
		mininet> h1 ping h9 -c 25
	latency_h7-h9.txt
		mininet> h7 ping h9 -c 25
	throughput_h1-h4-txt
		h4> python3 simpleperf/simpleperf.py -s -I <h4_address>
		h1> python3 simpleperf/simpleperf.py -c -b <h4_address>
	throughput_h1-h9.txt
		h9> python3 simpleperf/simpleperf.py -s -b <h9_address>
		h1> python3 simpleperf/simpleperf.py -c -I <h9_address>
	throughput_h1-h9.txt
		h9> python3 simpleperf/simpleperf.py -s -b <h9_address>
		h7> python3 simpleperf/simpleperf.py -c -I <h9_address>	

test-case-4
	latency_h1-h4-1.txt & latency_h2-h5-1.txt
		h1> ping <h4_address> -c 25
		h2> ping <h5_address> -c 25
	throughput_h1-h4-1.txt & throughput_h2-h5-1.txt
		h4> python3 simpleperf/simpleperf.txt -s -b <h4_address>
		h5> python3 simpleperf/simpleperf.txt -s -b <h5_address>
		h1> python3 simpleperf/simpleperf.txt -c -I <h4_address>
                h2> python3 simpleperf/simpleperf.txt -c -I <h5_address>
	
	latency_h1-h4-2.txt & latency_h2-h5-2.txt & latency_h3-h6-2.txt
                h1> ping <h4_address> -c 25
                h2> ping <h5_address> -c 25
		h3> ping <h6_address> -c 25
        throughput_h1-h4-2.txt & throughput_h2-h5-2.txt & throughput_h3-h6-2.txt
                h4> python3 simpleperf/simpleperf.txt -s -b <h4_address>
                h5> python3 simpleperf/simpleperf.txt -s -b <h5_address>
		h6> python3 simpleperf/simpleperf.txt -s -b <h6_address>
                h1> python3 simpleperf/simpleperf.txt -c -I <h4_address>
                h2> python3 simpleperf/simpleperf.txt -c -I <h5_address>
		h3> python3 simpleperf/simpleperf.txt -c -I <h6_address>

	latency_h1-h4-3.txt & latency_h7-h9-3.txt
                h1> ping <h4_address> -c 25
                h7> ping <h9_address> -c 25
        throughput_h1-h4-3.txt & throughput_h7-h9-3.txt
                h4> python3 simpleperf/simpleperf.txt -s -b <h4_address>
                h9> python3 simpleperf/simpleperf.txt -s -b <h9_address>
                h1> python3 simpleperf/simpleperf.txt -c -I <h4_address>
                h7> python3 simpleperf/simpleperf.txt -c -I <h9_address>

	latency_h1-h4-4.txt & latency_h8-h9-4.txt
                h1> ping <h4_address> -c 25
                h8> ping <h9_address> -c 25
        throughput_h1-h4-4.txt & throughput_h8-h9-4.txt
                h4> python3 simpleperf/simpleperf.txt -s -b <h4_address>
                h9> python3 simpleperf/simpleperf.txt -s -b <h9_address>
                h1> python3 simpleperf/simpleperf.txt -c -I <h4_address>
                h8> python3 simpleperf/simpleperf.txt -c -I <h9_address>

test-case-5
	throughput_h1-h4.txt
		h4> python3 simpleperf/simpleperf.txt -s -b <h4_address>
		h1> python3 simpleperf/simpleperf.txt -c -I <h4_address> -P 2
	throughput_h2-h5.txt
		h5> python3 simpleperf/simpleperf.txt -s -b <h5_address>
		h2> python3 simpleperf/simpleperf.txt -c -I <h5_address>
	throughput_h3-h6.txt
		h6> python3 simpleperf/simpleperf.txt -s -b <h6_address>
		h3> python3 simpleperf/simpleperf.txt -c -I <h6_address>

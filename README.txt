test-case-1
	throughput_udp_iperf_h1-h4.txt
		h1: iperf -c 10.0.5.2 -u -b 34M | tee measurements/test-case-1/throughput_udp_iperf_h1-h4.txt
		h2: iperf -s -u
	throughput_udp_iperf_h1-h9.txt
		h1: iperf -c 10.0.7.2 -u -b 20M | tee measurements/test-case-1/throughput_udp_iperf_h1-h9.txt
		h9: iperf -s -u
	throughput_udp_iperf_h7-h9.txt
		h7: iperf -c 10.0.7.2 -u -b 19M | tee measurements/test-case-1/throughput_udp_iperf_h7-h9.txt 
		h9: iperf -s -u
		

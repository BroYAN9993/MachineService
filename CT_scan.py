from rabbit import RabbitHole
from multiprocessing import Process


class AbstractMessage(object):
    def __len__(self):
        return 10
    def __getitem__(self, key):
        return self
    pass


class StartStudy(AbstractMessage):
    pass


class StartScan(AbstractMessage):
    pass


class CancelScan(AbstractMessage):
    pass


class ShowTableMoveHint(AbstractMessage):
    pass


class CancelTableMoveHint(AbstractMessage):
    pass


class ShowExposureHint(AbstractMessage):
    pass


class CancelExposureHint(AbstractMessage):
    pass


class ScanFinished(AbstractMessage):
    pass


class CTScanUpdate(AbstractMessage):
    pass


class Machine:
    def __init__(self, states, stdin, stdout):
        self.states = states
        self.stdin = stdin
        self.stdout = stdout

    def listen(self, msg_type, action):
        def runner(message):
            if isinstance(message, msg_type):
                action()

        self.stdin.run(runner)

    def listen_with_message(self, msg_type, action):
        def runner(message):
            if isinstance(message, msg_type):
                action(message)

        self.stdin.run(runner)


class MessageBus:
    def __init__(self, rabbit_hole: RabbitHole):
        self.rabbit_hole = rabbit_hole

    def run(self, call_back):
        self.rabbit_hole.get_consumer(call_back)

    def push(self, message):
        self.rabbit_hole.publish(message)


class Scan(Machine):
    def __init__(self, states, stdin, stdout):
        super().__init__(states=states, stdin=stdin, stdout=stdout)
        self.states = states
        self.stdin = self.stdin
        self.stdout = self.stdout
        self.listen(StartStudy, self.ready_scan)
        self.listen(StartScan, self.start_scan)
        self.listen(CancelScan, self.cancel_scan)
        self.listen(ShowTableMoveHint, self.display_table_move_hint)
        self.listen(CancelTableMoveHint, self.start_move_table)
        self.listen(ShowExposureHint, self.complete_table_move)
        self.listen(CancelExposureHint, self.start_exposure)
        self.listen(ScanFinished, self.complete_scan)
        self.listen(CTScanUpdate, self.display_states)

    def display_states(self):
        print(self.states)

    def send_update_message(self):
        self.stdout.push(CTScanUpdate())

    def ready_scan(self):
        self.send_update_message()

    def start_scan(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if self.is_first_unstarted_scan_of_study(scan_study_id, scan_id) and scan_state == 0:
                scan_state = 2
                self.send_update_message()

    def cancel_scan(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if scan_state in range(1, 6):
                scan_state = 0
                self.send_update_message()

    def display_table_move_hint(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if scan_state == 2:
                scan_state += 1
                self.send_update_message()

    def start_move_table(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if scan_state == 3:
                scan_state += 1
                self.send_update_message()

    def complete_table_move(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if scan_state == 4:
                scan_state += 1
                self.send_update_message()

    def start_exposure(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if scan_state == 5:
                scan_state += 1
                self.send_update_message()

    def complete_scan(self):
        for scan in self.states:
            scan_study_id, scan_id, scan_state = scan
            if scan_state == 6:
                scan_state += 1
                self.send_update_message()
                if self.is_not_last_scan_of_study(scan_study_id, scan_id):
                    self.ready_scan()

    def is_first_unstarted_scan_of_study(self, study_id, scan_id):
        for i in range(scan_id):
            if self.states[i][2] != 7:
                return False
        return True

    def is_not_last_scan_of_study(self, study_id, scan_id):
        return scan_id < len(self.states) - 1


def run_scan(mb: MessageBus):
    scan = Scan(states=Scans,
                stdin=mb,
                stdout=mb)


def push_message(mb: MessageBus):
    while True:
        input_data = input()
        if input_data == "start_study":
            mb.push(StartStudy())
        if input_data == "start_scan":
            mb.push(StartScan())
        if input_data == "cancel_scan":
            mb.push(CancelScan())
        if input_data == "show_table_hint":
            mb.push(ShowTableMoveHint())
        if input_data == "cancel_table_hint":
            mb.push(CancelTableMoveHint())
        if input_data == "show_exp_hint":
            mb.push(ShowExposureHint())
        if input_data == "cancel_exp_hint":
            mb.push(CancelExposureHint())
        if input_data == "scan_finished":
            mb.push(ScanFinished())
        if input_data == "scan_update":
            mb.push(CTScanUpdate())


if __name__ == "__main__":
    Scans = [[1, 0, 0], [1, 1, 0], [1, 2, 0], [1, 3, 0]]
    rb = RabbitHole(host="localhost", exchange="scan_bus")
    mb = MessageBus(rb)
    p1 = Process(target=run_scan, args=(mb,))
    p2 = Process(target=push_message, args=(mb,))
    p1.run()
    p2.run()
    p1.join()
    p2.join()

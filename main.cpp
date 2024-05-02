#include <iostream>
#include <vector>
#include <regex>

using namespace std;

const int I = 0, FLOORS = 6, ELEVATORS = 5;

/**
 * 表示每楼层外面板上的一个按钮
 */
struct Button {
    /**
     * 向上的按钮是否按下
     */
    bool up;
    /**
     * 向下的按钮是否按下
     */
    bool down;
    /**
     * 想向上的人数
     */
    int upCnt = 0;
    /**
     * 想向下的人数
     */
    int downCnt = 0;

    Button() {}

    Button(const bool &u, const bool &d, const int &iu, const int &id)
            : up(u), down(d), upCnt(iu), downCnt(id) {}
};

/**
 * 表示一个矫箱
 */
struct Elevator {
    /**
     * 表示是否有人
     */
    int status;
    /**
     * 所在楼层
     */
    int level;
    /**
     * 自动移动方向，0向下，1向上
     */
    int autoModeFace; // 0 -> down, 1 -> up
    /**
     * 电梯是否满员
     */
    bool isFull;
    /**
     * 矫箱内按钮是否按下。
     * 当btn[x] == y时，去y楼的按钮被按下
     */
    int btn[FLOORS];

    Elevator() {}

    Elevator(const size_t &o, const int &s, const int &l, const int &a, const bool &i)
            : status(s), level(l), autoModeFace(a), isFull(i) {}
};

vector<Button> buttons(FLOORS);
vector<Elevator> elevators(ELEVATORS);

struct elevatorGame {
    size_t roundId;

    elevatorGame() {}

    void newGame() {
        roundId += 1;
        for (int i = 0; i < FLOORS; i++)
            buttons[i] = Button(false, false, 0, 0);
        for (int i = 0; i < ELEVATORS; i++)
            elevators[i] = Elevator(I, 0, 0, 0, false);
    }

    void getInfo() {
        string directions, persons_up, persons_down, is_full, is_pressed;
        for (int i = 1; i <= FLOORS; i++) {
            cin >> directions >> persons_up >> persons_down;
            buttons[i] = Button(directions[0] == '1', directions[1] == '1', stoi(persons_up), stoi(persons_down));
        }

        for (int i = 1; i <= ELEVATORS; i++) {
            cin >> persons_up >> persons_down >> is_full >> is_pressed;
            int occupied = persons_up[0] == '1', level = stoi(persons_down);
            int auto_face_mode = persons_up[1] == '1', is_full_int = stoi(is_full);
            auto_face_mode = occupied ? auto_face_mode : 2; // 这啥鸡巴意思
            elevators[i] = Elevator(I, occupied, level, auto_face_mode, is_full_int);
            for (size_t p = 0; p < is_pressed.size(); p++)
                elevators[i].btn[p + 1] = is_pressed[p] == '1';
        }
    }
} GAME;

inline int dis(Elevator elevator, int floor) {
    return abs(elevator.level - floor - 1);
}

inline bool available(Elevator ele) {
    return !ele.status;
}

inline bool pressed(Button btn) {
    return btn.down || btn.up;
}

string yourTurn() {
    string res(ELEVATORS, 'S');
    vector<int> closest_avail;
    int floor_num[buttons.size()], elevator_num[elevators.size()];
    int available_elevators = 0, busy_floors = 0;

    for (int e = 0; e < ELEVATORS; ++e) {
        if (available(elevators[e])) {
            elevator_num[available_elevators++] = e;
        }
    }
    for (int floor = 0; floor < FLOORS; ++floor) {
        if (pressed(buttons[floor])) {
            floor_num[busy_floors++] = floor;
            closest_avail.push_back(0);
        }
    }

    for (int f_i = 0; f_i < busy_floors; ++f_i) {
        for (int e_i = 1; e_i < available_elevators; ++e_i) {
            if (dis(elevators[e_i], floor_num[f_i]) < closest_avail[floor_num[f_i]]) {
                bool duplicated = false;
                for (int j = 0; j < f_i; ++j) {
                    // duplication solver
                    // closest_available can't have duplicated values
                    if (closest_avail[j] == e_i) {
                        duplicated = true;
                        break;
                    }
                }
                if (!duplicated) {
                    closest_avail[f_i] = elevator_num[e_i];
                }
            }
        }
    }

    for (int f_i = 0; f_i < busy_floors; ++f_i) {
        int floor = floor_num[f_i];
        int e_i = closest_avail[f_i];
        res[e_i] = floor <= elevators[e_i].level ? 'D' : 'U';
    }
    return res;
}

int main() {
    while (true) {
        string first;
        cin >> first;
        if (first == "N")
            GAME.newGame();
        GAME.getInfo();
        string str = yourTurn();
        transform(str.begin(), str.end(), str.begin(), [](unsigned char c) { return toupper(c); });
        regex r("[A-Z]");
        for (sregex_iterator it = sregex_iterator(str.begin(), str.end(), r);
             it != sregex_iterator();
             ++it) {
            smatch match = *it;
            cout << match.str() << " ";
        }
        cout << endl;
    }
    return 0;
}

#include <iostream>
#include <vector>
#include <regex>

using namespace std;

const int I = 0, __SZ = 10;

struct Button
{
    bool up;
    bool down;
    int upCnt = 0;
    int downCnt = 0;

    Button() {}
    Button(const bool &u, const bool &d, const int &iu, const int &id)
            : up(u), down(d), upCnt(iu), downCnt(id) {}
};

struct Elevator
{
    int status;
    int level;
    int autoModeFace; // 0 -> down, 1 -> up
    bool isFull;
    int btn[__SZ];

    Elevator() {}
    Elevator(const size_t &o, const int &s, const int &l, const int &a, const bool &i)
            : status(s), level(l), autoModeFace(a), isFull(i) {}
};

vector<Button> buttons(__SZ);
vector<Elevator> elevators(__SZ);

struct elevatorGame
{
    size_t roundId;

    elevatorGame() {}

    void __newGame()
    {
        roundId += 1;
        for (int i = 0; i < __SZ; i++)
            buttons[i] = Button(false, false, 0, 0);
        for (int i = 0; i < __SZ; i++)
            elevators[i] = Elevator(I, 0, 0, 0, false);
    }

    void __getInfo()
    {
        string __buttons, __a, __b, __c, __d;
        for (int i = 1; i <= 6; i++)
        {
            cin >> __buttons >> __a >> __b;
            buttons[i] = Button(__buttons[0] == '1', __buttons[1] == '1', stoi(__a), stoi(__b));
        }

        for (int i = 1; i <= 5; i++)
        {
            cin >> __a >> __b >> __c >> __d;
            int a = __a[0] == '1', b = stoi(__b);
            int c = __a[1] == '1', d = stoi(__c);
            c = a ? c : 2;
            elevators[i] = Elevator(I, a, b, c, d);
            for (size_t p = 0; p < __d.size(); p++)
                elevators[i].btn[p + 1] = __d[p] == '1';
        }
    }
} GAME;

string yourTurn()
{
    /********************修改本函数，以下为示例***************/
    string res(" UUUUU");

    int bid = 1;
    buttons[bid].down;    // bool 这层是否有人希望向下
    buttons[bid].up;      // bool 这层是否有人希望向上
    buttons[bid].upCnt;   // int  这层有多少人希望向上
    buttons[bid].downCnt; // itn  这层有多少人希望向下

    int eid = 1;
    elevators[eid].status;       // 这台电梯里有没有人
    elevators[eid].level;        // 这台电梯的楼层
    elevators[eid].autoModeFace; // 这台电梯的移动方向
    elevators[eid].isFull;       // 这台电梯是否满员

    elevators[eid].btn[1]; // bool 这台电梯是否有人前往 1 层
    elevators[eid].btn[2]; // bool 这台电梯是否有人前往 2 层
    // ...
    elevators[eid].btn[6]; // bool 这台电梯是否有人前往 6 层

    int i = 1;
    // 让第 i 台电梯向上
    res[i] = 'U';
    // 让第 i 台电梯向下
    res[i] = 'D';
    // 让第 i 台电梯停留
    res[i] = 'S';

    return res;
}

int main()
{
    while (true)
    {
        string first;
        cin >> first;
        if (first == "N")
            GAME.__newGame();
        GAME.__getInfo();
        string str = yourTurn();
        transform(str.begin(), str.end(), str.begin(), [](unsigned char c)
        { return toupper(c); });
        regex r("[A-Z]");
        for (sregex_iterator it = sregex_iterator(str.begin(), str.end(), r);
             it != sregex_iterator();
             ++it)
        {
            smatch match = *it;
            cout << match.str() << " ";
        }
        cout << endl;
    }
    return 0;
}

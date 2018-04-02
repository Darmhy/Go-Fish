#include <iostream>
#include "ofxMSAmcts.h"
using namespace std;

int main(){
	msa::LoopTimer timer;
	timer.test(1000);

    cout << "hello world";

	system("pause");
    return 0;
}
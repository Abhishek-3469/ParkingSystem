#include <vector>
#include <string>
#include <opencv2/opencv.hpp>
#include <tesseract/baseapi.h>

// ==========================================
// BASE64 ENCODER (To send video over terminal)
// ==========================================
static const std::string base64_chars = 
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789+/";

std::string base64_encode(unsigned char const* bytes_to_encode, unsigned int in_len) {
    std::string ret;
    int i = 0, j = 0;
    unsigned char char_array_3[3], char_array_4[4];

    while (in_len--) {
        char_array_3[i++] = *(bytes_to_encode++);
        if (i == 3) {
            char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
            char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
            char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
            char_array_4[3] = char_array_3[2] & 0x3f;

            for(i = 0; i < 4; i++) ret += base64_chars[char_array_4[i]];
            i = 0;
        }
    }

    if (i) {
        for(j = i; j < 3; j++) char_array_3[j] = '\0';
        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
        char_array_4[3] = char_array_3[2] & 0x3f;

        for (j = 0; j < i + 1; j++) ret += base64_chars[char_array_4[j]];
        while((i++ < 3)) ret += '=';
    }
    return ret;
}

// ==========================================
// Tesseract & OpenCV Engine
// ==========================================
tesseract::TessBaseAPI* ocr = new tesseract::TessBaseAPI();

cv::Mat extractAndReadPlate(cv::Mat& frame) {
    cv::Mat gray, blur, edges;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    cv::bilateralFilter(gray, blur, 11, 17, 17); 
    cv::Canny(blur, edges, 30, 200);

    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(edges, contours, cv::RETR_TREE, cv::CHAIN_APPROX_SIMPLE);

    std::sort(contours.begin(), contours.end(), 
            [](const std::vector<cv::Point>& a, const std::vector<cv::Point>& b) {
                return cv::contourArea(a) > cv::contourArea(b);
            });

    std::vector<cv::Point> plateContour;
    bool plateFound = false;

    for (size_t i = 0; i < contours.size() && i < 10; i++) {
        std::vector<cv::Point> approx;
        cv::approxPolyDP(contours[i], approx, 0.018 * cv::arcLength(contours[i], true), true);

        if (approx.size() == 4) {
            plateContour = approx;
            plateFound = true;
            break;
        }
    }

    if (plateFound) {
        cv::polylines(frame, plateContour, true, cv::Scalar(0, 255, 0), 3);

        cv::Rect boundingBox = cv::boundingRect(plateContour);
        boundingBox &= cv::Rect(0, 0, frame.cols, frame.rows);
        cv::Mat croppedPlate = gray(boundingBox);

        cv::Mat processedPlate;
        cv::resize(croppedPlate, processedPlate, cv::Size(), 2.0, 2.0, cv::INTER_CUBIC);
        cv::threshold(processedPlate, processedPlate, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU);

        ocr->SetImage(processedPlate.data, processedPlate.cols, processedPlate.rows, 1, processedPlate.step);
        std::string plateText = std::string(ocr->GetUTF8Text());
        
        plateText.erase(std::remove_if(plateText.begin(), plateText.end(), [](char c) {
            return !std::isalnum(c); 
    }), plateText.end());

        if (!plateText.empty() && plateText.length() > 3) {
            std::cout << "\n>>> SCANNED VRN:" << plateText << "<<<" << std::endl;
        }
    }

    return frame;
}

int main() {
// UPDATED: Using the relative path inside the master folder
    if (ocr->Init("ANPR_Project/tessdata", "eng")) {
        std::cerr << "Could not initialize Tesseract." << std::endl;
        return -1;
    }
    ocr->SetVariable("tessedit_char_whitelist", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789");

    cv::VideoCapture cap(0); 
    if (!cap.isOpened()) return -1;

    cap.set(cv::CAP_PROP_FRAME_WIDTH, 640);
    cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

    cv::Mat frame;
    std::cout << "Level 2 ANPR Web Stream Engine Online. Awaiting vehicles..." << std::endl;

    while (true) {
        cap >> frame; 
        if (frame.empty()) break;

        frame = extractAndReadPlate(frame);

        std::vector<uchar> buf;
        std::vector<int> params = {cv::IMWRITE_JPEG_QUALITY, 50}; 
        cv::imencode(".jpg", frame, buf, params);
        
        std::string base64_string = base64_encode(buf.data(), buf.size());
        std::cout << ">>> FRAME:" << base64_string << std::endl;

        if (cv::waitKey(1) == 27) break;
    }

    ocr->End();
    cap.release();
    cv::destroyAllWindows();
    return 0;
}
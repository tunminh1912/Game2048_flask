from flask import Flask, render_template, jsonify, request
import random
import mysql.connector


app = Flask(__name__)

# Initialize game variables
VAL_CHOICE = [2, 4]
souc = 0
ds = []
current_user = None  # Biến toàn cục để lưu trữ người dùng hiện tại

def connect_to_mysql():
    # Thay thông tin kết nối cho phù hợp với MySQL của bạn
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="2048"
    )

def init_matrix():
    global ds
    ds = [[0 for _ in range(4)] for _ in range(4)]
    for _ in range(2):
        add_block()
    return ds

def add_block():
    while True:
        i = random.randint(0, 3)
        j = random.randint(0, 3)
        if ds[i][j] == 0:
            ds[i][j] = random.choice(VAL_CHOICE)
            break

def move_left():
    global souc
    moved = False
    for i in range(4):
        new_row = [x for x in ds[i] if x != 0]
        combined_row = []
        j = 0
        while j < len(new_row):
            if j + 1 < len(new_row) and new_row[j] == new_row[j + 1]:
                combined_row.append(new_row[j] * 2)
                souc += new_row[j] * 2
                j += 2
            else:
                combined_row.append(new_row[j])
                j += 1
        combined_row += [0] * (4 - len(combined_row))
        if combined_row != ds[i]:
            moved = True
        ds[i] = combined_row
    return moved

def move_right():
    global souc
    moved = False
    for i in range(4):
        # Combine tiles and move right
        new_row = [x for x in ds[i] if x != 0][::-1]
        combined_row = []
        j = 0
        while j < len(new_row):
            if j + 1 < len(new_row) and new_row[j] == new_row[j + 1]:
                combined_row.append(new_row[j] * 2)
                souc += new_row[j] * 2
                j += 2  # Skip the next tile
            else:
                combined_row.append(new_row[j])
                j += 1
        combined_row += [0] * (4 - len(combined_row))  # Fill the rest with zeros
        combined_row.reverse()  # Reverse to original order
        if combined_row != ds[i]:
            moved = True
        ds[i] = combined_row
    return moved

def move_up():
    global souc
    moved = False
    for j in range(4):
        # Combine tiles and move up
        new_column = [ds[i][j] for i in range(4) if ds[i][j] != 0]
        combined_column = []
        k = 0
        while k < len(new_column):
            if k + 1 < len(new_column) and new_column[k] == new_column[k + 1]:
                combined_column.append(new_column[k] * 2)
                souc += new_column[k] * 2
                k += 2
            else:
                combined_column.append(new_column[k])
                k += 1
        combined_column += [0] * (4 - len(combined_column))  # Fill the rest with zeros
        for i in range(4):
            if i < len(combined_column):
                if combined_column[i] != ds[i][j]:
                    moved = True
                ds[i][j] = combined_column[i]
            else:
                ds[i][j] = 0
    return moved

def move_down():
    global souc
    moved = False
    for j in range(4):
        # Combine tiles and move down
        new_column = [ds[i][j] for i in range(4) if ds[i][j] != 0][::-1]
        combined_column = []
        k = 0
        while k < len(new_column):
            if k + 1 < len(new_column) and new_column[k] == new_column[k + 1]:
                combined_column.append(new_column[k] * 2)
                souc += new_column[k] * 2
                k += 2  # Skip the next tile
            else:
                combined_column.append(new_column[k])
                k += 1
        combined_column += [0] * (4 - len(combined_column))  # Fill the rest with zeros
        combined_column.reverse()  # Reverse to original order
        for i in range(4):
            if i < len(combined_column):
                if combined_column[i] != ds[i][j]:
                    moved = True
                ds[i][j] = combined_column[i]
            else:
                ds[i][j] = 0
    return moved
def check_win():
    for row in ds:
        if 2048 in row:
            return True
    return False

def check_loss():
    for i in range(4):
        for j in range(4):
            if ds[i][j] == 0:
                return False
            if i < 3 and ds[i][j] == ds[i + 1][j]:
                return False
            if j < 3 and ds[i][j] == ds[i][j + 1]:
                return False
    return True

def updateBXH(score):
    db = connect_to_mysql()
    cursor = db.cursor()

    # Kiểm tra nếu điểm số mới cao hơn điểm số hiện tại trong bảng xếp hạng
    cursor.execute("SELECT score FROM bxh WHERE username = %s", (current_user,))
    existing_score = cursor.fetchone()

    if existing_score:
        # Nếu điểm số cũ thấp hơn, cập nhật điểm mới
        if existing_score[0] < score:
            cursor.execute("UPDATE bxh SET score = %s WHERE username = %s", (score, current_user))
            db.commit()
    else:
        # Nếu chưa có điểm của người chơi, thêm mới
        cursor.execute("INSERT INTO bxh (username, score) VALUES (%s, %s)", (current_user, score))
        db.commit()

    # Giữ lại top 10 điểm cao nhất
    cursor.execute("DELETE FROM bxh WHERE id NOT IN (SELECT id FROM (SELECT id FROM bxh ORDER BY score DESC LIMIT 10) AS t)")
    db.commit()

    cursor.close()
    db.close()



def get_high_score(username):
    db = connect_to_mysql()
    cursor = db.cursor()
    cursor.execute("SELECT MAX(score) FROM bxh WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result[0] if result[0] else 0


@app.route('/rank')
def rank():
    # Kết nối tới cơ sở dữ liệu
    db = connect_to_mysql()
    cursor = db.cursor(dictionary=True)

    # Lấy danh sách top 10 điểm cao nhất
    cursor.execute("SELECT * FROM bxh ORDER BY score DESC LIMIT 10")
    ranks = cursor.fetchall()

    # Đóng kết nối
    cursor.close()
    db.close()

    print(ranks)
    # Truyền dữ liệu bảng xếp hạng vào template
    return render_template('rank.html', ranks=ranks)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    global ds, souc, current_user
    current_user = request.json.get('username')  # Lấy tên người chơi từ yêu cầu
    ds = init_matrix()  # Khởi tạo ma trận mới
    souc = 0  # Đặt lại điểm số
    high_score = get_high_score(current_user)
    return jsonify({'matrix': ds, 'score': souc, 'high_score': high_score, 'status': 'ongoing'})

@app.route('/move/<direction>')
def move(direction):
    global ds, souc
    moved = False
    if direction == 'left':
        moved = move_left()
    elif direction == 'right':
        moved = move_right()
    elif direction == 'up':
        moved = move_up()
    elif direction == 'down':
        moved = move_down()

    if moved:
        add_block()

    # Kiểm tra trạng thái trò chơi
    if check_win():
        updateBXH(souc)  # Cập nhật bảng xếp hạng khi người chơi thắng
        high_score = get_high_score(current_user)
        return jsonify({'status': 'win', 'score': souc, 'high_score': high_score})

    if check_loss():
        updateBXH(souc)  # Cập nhật bảng xếp hạng khi game over
        high_score = get_high_score(current_user)
        return jsonify({'status': 'gameover', 'score': souc, 'high_score': high_score})

    # Nếu trò chơi tiếp tục
    return jsonify({'matrix': ds, 'score': souc, 'status': 'ongoing'})

def game_over():
    # Kiểm tra điều kiện kết thúc game
    for i in range(4):
        for j in range(4):
            if ds[i][j] == 0:  # Nếu còn ô trống, chưa game over
                return False
    for i in range(4):
        for j in range(4):
            if i < 3 and ds[i][j] == ds[i + 1][j]:  # Kiểm tra cột
                return False
            if j < 3 and ds[i][j] == ds[i][j + 1]:  # Kiểm tra hàng
                return False
    return True


if __name__ == '__main__':
    app.run(debug=True)
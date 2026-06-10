"""火影忍者手游论坛 —— Flask 后端"""

import sqlite3
import functools
from datetime import datetime
from flask import Flask, g, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

# ── 初始化 ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "naruto-forum-secret-key-2024"  # 实际部署时请更换

DATABASE = "forum.db"


# ── 数据库工具 ──────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """初始化数据库表"""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            is_pinned INTEGER DEFAULT 0,
            is_elite INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        );
    """)
    db.commit()

    # 如果没有管理员，创建一个默认管理员
    admin = db.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
            ("admin", generate_password_hash("admin123")),
        )
        db.commit()


# ── 登录装饰器 ──────────────────────────────────────────────────────────
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("权限不足", "danger")
            return redirect(url_for("index"))
        return view(**kwargs)
    return wrapped_view


# ── 上下文处理器 ────────────────────────────────────────────────────────
@app.context_processor
def inject_user():
    """在每个模板中注入当前登录用户信息"""
    if "user_id" in session:
        return {
            "current_user": {
                "id": session["user_id"],
                "username": session["username"],
                "is_admin": session.get("is_admin", False),
            }
        }
    return {"current_user": None}


# ══════════════════════════════════════════════════════════════════════
#                           页  面  路  由
# ══════════════════════════════════════════════════════════════════════

# ── 首页：帖子列表 ──────────────────────────────────────────────────────
@app.route("/")
def index():
    db = get_db()
    search = request.args.get("q", "").strip()

    if search:
        posts = db.execute(
            """SELECT p.*, u.username,
                      (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
               FROM posts p JOIN users u ON p.user_id = u.id
               WHERE p.title LIKE ? OR p.content LIKE ?
               ORDER BY p.is_pinned DESC, p.created_at DESC""",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        posts = db.execute(
            """SELECT p.*, u.username,
                      (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
               FROM posts p JOIN users u ON p.user_id = u.id
               ORDER BY p.is_pinned DESC, p.created_at DESC""",
        ).fetchall()

    return render_template("index.html", posts=posts, search=search)


# ── 注册 ────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm"]

        if not username or not password:
            flash("用户名和密码不能为空", "danger")
        elif len(username) < 2 or len(username) > 20:
            flash("用户名长度需在 2-20 个字符之间", "danger")
        elif len(password) < 4:
            flash("密码至少 4 个字符", "danger")
        elif password != confirm:
            flash("两次密码输入不一致", "danger")
        else:
            db = get_db()
            if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
                flash("用户名已存在", "danger")
            else:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                flash("注册成功，请登录", "success")
                return redirect(url_for("login"))

    return render_template("register.html")


# ── 登录 ────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            flash("用户名不存在", "danger")
        elif user["is_banned"]:
            flash("该账号已被封禁", "danger")
        elif not check_password_hash(user["password_hash"], password):
            flash("密码错误", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            flash(f"欢迎回来，{user['username']}！", "success")
            return redirect(url_for("index"))

    return render_template("login.html")


# ── 退出 ────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("index"))


# ── 发帖 ────────────────────────────────────────────────────────────────
@app.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()

        if not title:
            flash("标题不能为空", "danger")
        elif not content:
            flash("内容不能为空", "danger")
        else:
            db = get_db()
            db.execute(
                "INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)",
                (title, content, session["user_id"]),
            )
            db.commit()
            flash("发帖成功！", "success")
            return redirect(url_for("index"))

    return render_template("create_post.html")


# ── 帖子详情 + 回帖 ────────────────────────────────────────────────────
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def view_post(post_id):
    db = get_db()
    post = db.execute(
        """SELECT p.*, u.username
           FROM posts p JOIN users u ON p.user_id = u.id
           WHERE p.id = ?""",
        (post_id,),
    ).fetchone()

    if post is None:
        flash("帖子不存在", "warning")
        return redirect(url_for("index"))

    # 增加浏览量
    db.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = ?", (post_id,))
    db.commit()

    # 处理回帖
    if request.method == "POST" and "user_id" in session:
        content = request.form["content"].strip()
        if content:
            db.execute(
                "INSERT INTO comments (content, user_id, post_id) VALUES (?, ?, ?)",
                (content, session["user_id"], post_id),
            )
            db.commit()
            flash("回复成功！", "success")
        else:
            flash("回复内容不能为空", "danger")
        return redirect(url_for("view_post", post_id=post_id))

    # 获取回帖列表
    comments = db.execute(
        """SELECT c.*, u.username
           FROM comments c JOIN users u ON c.user_id = u.id
           WHERE c.post_id = ?
           ORDER BY c.created_at ASC""",
        (post_id,),
    ).fetchall()

    return render_template("post.html", post=post, comments=comments)


# ── 删除帖子（管理员） ──────────────────────────────────────────────────
@app.route("/post/<int:post_id>/delete", methods=["POST"])
@admin_required
def delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("帖子已删除", "success")
    return redirect(url_for("index"))


# ── 删除回帖（管理员） ─────────────────────────────────────────────────
@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@admin_required
def delete_comment(comment_id):
    db = get_db()
    comment = db.execute("SELECT post_id FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if comment:
        db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        db.commit()
        flash("回复已删除", "success")
        return redirect(url_for("view_post", post_id=comment["post_id"]))
    flash("回复不存在", "warning")
    return redirect(url_for("index"))


# ── 置顶/取消置顶（管理员） ───────────────────────────────────────────
@app.route("/post/<int:post_id>/pin", methods=["POST"])
@admin_required
def toggle_pin(post_id):
    db = get_db()
    post = db.execute("SELECT is_pinned FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post:
        new = 0 if post["is_pinned"] else 1
        db.execute("UPDATE posts SET is_pinned = ? WHERE id = ?", (new, post_id))
        db.commit()
        flash("已置顶" if new else "已取消置顶", "success")
    return redirect(url_for("index"))


# ── 管理员后台 ──────────────────────────────────────────────────────────
@app.route("/admin")
@admin_required
def admin_panel():
    db = get_db()

    users = db.execute(
        "SELECT id, username, is_admin, is_banned, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()

    posts = db.execute(
        """SELECT p.*, u.username
           FROM posts p JOIN users u ON p.user_id = u.id
           ORDER BY p.created_at DESC"""
    ).fetchall()

    return render_template("admin.html", users=users, posts=posts)


# ── 封禁/解封用户（管理员） ────────────────────────────────────────────
@app.route("/admin/user/<int:user_id>/toggle_ban", methods=["POST"])
@admin_required
def toggle_ban(user_id):
    db = get_db()
    user = db.execute("SELECT is_banned FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        new = 0 if user["is_banned"] else 1
        db.execute("UPDATE users SET is_banned = ? WHERE id = ?", (new, user_id))
        db.commit()
        flash("已解封" if not new else "已封禁", "success")
    return redirect(url_for("admin_panel"))


# ── 删除用户（管理员） ──────────────────────────────────────────────────
@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == session["user_id"]:
        flash("不能删除自己", "danger")
        return redirect(url_for("admin_panel"))

    db = get_db()
    # 删除该用户的所有帖子和评论
    db.execute("DELETE FROM comments WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM posts WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("用户已删除", "success")
    return redirect(url_for("admin_panel"))


# ══════════════════════════════════════════════════════════════════════
#                           启  动  项  目
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

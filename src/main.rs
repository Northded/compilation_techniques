use regex::Regex;
use std::{env, fs, process};

fn check_unclosed_comments(source: &str) -> Result<(), String> {
    let open = source.matches("/*").count();
    let close = source.matches("*/").count();
    if open > close {
        return Err(format!("Незакрытый многострочный комментарий (найдено {} '/*' и {} '*/')", open, close));
    }
    if close > open {
        return Err(format!("Лишний символ закрытия '*/' (найдено {} '/*' и {} '*/')", open, close));
    }
    Ok(())
}

fn check_invalid_chars(source: &str) -> Result<(), String> {
    for (i, ch) in source.char_indices() {
        if (ch as u32) < 32 && ch != '\t' && ch != '\n' && ch != '\r' {
            return Err(format!("Недопустимый символ (U+{:04X}) на позиции {}", ch as u32, i));
        }
    }
    Ok(())
}

fn preprocess(source: &str) -> String {
    // Удаление многострочных комментариев /* ... */
    let re_multi = Regex::new(r"(?s)/\*.*?\*/").unwrap();

    // Удаление однострочных комментариев // ...
    let re_single = Regex::new(r"(?m)//.*$").unwrap();

    // Замена нескольких пробелов/табуляций на один пробел
    let re_spaces = Regex::new(r"[ \t]+").unwrap();

    let s = re_multi.replace_all(source, "");
    let s = re_single.replace_all(&s, "");

    // Обрезка краёв строк, удаление пустых строк
    s.lines()
        .map(|line| re_spaces.replace_all(line.trim(), " ").to_string())
        .filter(|line| !line.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Использование: preprocessor <файл>");
        process::exit(1);
    }

    let source = fs::read_to_string(&args[1]).unwrap_or_else(|e| {
        eprintln!("Ошибка чтения файла: {}", e);
        process::exit(1);
    });

    if let Err(e) = check_invalid_chars(&source) {
        eprintln!("Ошибка: {}", e);
        process::exit(1);
    }

    if let Err(e) = check_unclosed_comments(&source) {
        eprintln!("Ошибка: {}", e);
        process::exit(1);
    }

    println!("{}", preprocess(&source));
    eprintln!("Ошибок не выявлено.");
}
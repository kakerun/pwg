#!/usr/bin/perl

# pwg.cgi
# 2012/06/20 Password Generator

###  使い方
# パラメータ:
# name		:ID,ユーザー名,メールアドレス
# site		:ドメイン
# 3piece	:適当に3文字
# pattern	:パターン 現在5つ
#  P	重要		:ドメイン名の数を4進数化して位を反転
#							その数字を0の箇所に当てはめる
#							最初の数字だけbから右へ移動
#							移動先の文字を次の数字分だけずらす
#							（ただし、次の数字が0の場合はdをaにする
#							（Lにかぶった場合、Lは小文字でずらし、nを大文字にする
#							3pieceを反転し次の数字に当てはまる箇所を大文字化する
#							最後に先頭から最初の数字の位置に3pieceを挿入する
#  B	頻繁		:3pieceを数字の箇所にちりばめる
#  P2	二重		:そのまま
#  8	八字		:8文字までしか設定できないサイト用
#  D	直接		:3pieceがそのままパスワードになる
# listview			:リストを見るためのパスワード
#
# Generate&Refresh	:登録&更新ボタン
# Clear				:知らない

use strict;
use CGI qw/-no_xhtml :standard/;
use CGI::Carp qw/fatalsToBrowser/;
charset('UTF-8');

# リテラル・初期設定
my $DATA      = 'pwf.dat';						#保存ファイル名
my $TITLE     = 'Password Generator';			#タイトル
my $ANONYMOUS = 'k';							#管理社名
my $PAGESIZE  = 300;							#1ページに表示する量
my $TOP_TEXT  = 'setumei';				#説明文
my $PREV_TEXT = escapeHTML('<<');				#戻る
my $NEXT_TEXT = escapeHTML('>>');				#次へ
my $REFERER   = 'http://www.example.com/pwg/';	#設置するREFERERに変更する
my $LVPASSWORD= 'password';						#一覧表示用パスワード

my @selectptrns = ("P","B","P2","8","D");		#パターン一覧
my $defaultptrn = 'P';							#デフォルトパターン


# パラメータ取得　初期値もあるよ
my $name = param('name') || $ANONYMOUS;			#ネーム
my $site = param('site') || '';					#サイト
my $piece = param('piece') || '';				#サイト3文字
my $ptrn = param('ptrn') || 'P';				#パターン 5個くらい
my $page = param('page') || '1';				#ページ
my $mess = param('mess') || '';					#注釈
my $lvpass = param('lvpass') || '';				#一覧表示用パスワード

if($name && $site && $piece){					#サイトがあったら
	(referer =~ /^$REFERER/) or die("不正なアクセスです\n");	#不正アクセス
	$name = escapeHTML($name);					#ネーム入れ
	$site = escapeHTML($site);					#サイト入れ
	$ptrn = escapeHTML($ptrn);					#パターン入れ
	$piece = escapeHTML($piece);				#3文字入れ
	$mess =~ s/\r\n|\r|\n/br/eg;				#改行やらなんやらの整合性
}
$lvpass = escapeHTML($lvpass);

my $pass;
if($site && $piece){
	$pass = $site.",".$piece;
	if($ptrn eq $selectptrns[0]){
		$pass = pwcreate0($pass);
	}elsif($ptrn eq $selectptrns[1]){
		$pass = pwcreate1($pass);
	}elsif($ptrn eq $selectptrns[2]){
		$pass = 'password';
	}elsif($ptrn eq $selectptrns[3]){
		$pass = 'passw'.$piece;
	}else{
		$pass = $piece;
	}
}

#ファイルが無い場合に自動的に作成
filecreate($DATA);

#ファイルがあること前提の書き込みオープン
open(FH, "+< $DATA") or die("ファイルのオープンに失敗しました\n");
flock(FH, 2);			#排他的処理；ファイルをロックする。後から来た人が待つ
1 while <FH>;			#最終行まで繰り返して移動
my $no = $.;			#最終行ナンバーを入れる
print FH ++$no, "\t", time, "\t$name\t$site\t$piece\t$ptrn\t$pass\t$mess\n" if($site && $piece);	#書き込み
close(FH);				#ファイルクローズ

# ページナビ
my $end   = $page * $PAGESIZE;			#1x3=3		2x3=6
my $start = $end - $PAGESIZE + 1;		#3-3+1=1	6-3+1=4
$end = $no if($no < $end);				#最終Noよりendの方が大きかったら end=3のまま
#start=10-3+1=8	end=10-1+1=10
($start, $end) = ($no - $end + 1, $no - $start + 1);

my(@page, $i);			#@pageと$i宣言
my $prev = $page - 1;	#1-1=0
my $next = $page + 1;	#1+1=2
#ページが1だったらリンク無し"<<"  1以外は戻れる"<<"
push(@page, ($page==1) ? $PREV_TEXT : a({href=>"?page=$prev"}, $PREV_TEXT));
#i=1から i<=((10-1)/3)+1=4
for($i=1; $i<=int(($no-1) / $PAGESIZE) + 1; $i++){
		#ページがiだったらi 違ったら他のページへ飛べるリンク付き
		push(@page, ($page==$i) ? $i : a({href=>"?page=$i"}, $i));
}
#ページが最終ページだったらリンク無し">>" 最終ページ以外は次のページへ行ける">>"
push(@page, ($page+1==$i) ? $NEXT_TEXT : a({href=>"?page=$next"}, $NEXT_TEXT));
#ページ数量が2より多かったら ページを空白で連結して区切って線引く
my $navi = ($i > 2) ? join(' ', @page).hr :'';

# データ取得
my(@data, $idx);	#@dataと$idx宣言
open(FH, "< $DATA") or die("読み込みオープンに失敗しました\n");	#読み込みオープン
while(<FH>){	#最終行までループ
	$idx++;	#idxを足していく　つまり最初=1
	if($start <= $idx && $end >= $idx){	#8<=1&&10>=1 1ページ目だと8～10のみ
		my($no, $time, $name, $site, $piece, $ptrn, $pass, $mess) = split(/\t/);	#区切って入れる
		my $timestr = localtime($time);	#表示できる時間に変換
		#メールが入力されていれば名前にメールリンク入れる
		#表示できるように成形
		push(@data, div($no.' : '.strong($site).' : '.strong($name).' : '.
				strong($pass).' : '.$piece).br.div($mess).hr);
	}
}
close(FH);	#ファイルクローズ


# 画面表示
print header(-charset => "UTF-8");
print start_html({title=>$TITLE, lang=>'ja'});
print h1($TITLE).hr;
print $TOP_TEXT.hr;
#サブミット押したらmsgboxでるフォーム作成
#print start_form({name=>'pwgform',onsubmit=>'return fldchk();'});
print start_form;
#ネーム
#print 'name'.popup_menu(
#	-name=>'name',
#	-values=>[$selectnames[0],$selectnames[1],$selectnames[2],
#	$selectnames[3],$selectnames[4]],
#	-default=>$defaultname);
print 'name'.textfield({name=>'name', value=>$name, size=>10});
#サイト
print 'site'.textfield({name=>'site', value=>$site, size=>10});
#サイト3文字
print '3piece'.textfield({name=>'piece', value=>$piece, size=>2});
#パターン
print 'pattern'.popup_menu(
	-name=>'ptrn',
	-values=>[$selectptrns[0],$selectptrns[1],$selectptrns[2],
			$selectptrns[3],$selectptrns[4]],
	-default=>$defaultptrn).br;
#注釈
print textarea({name=>'mess', rows=>2, cols=>50, default=>$mess, override=>1}).br;
#print 'ptrn'.textfield({name=>'ptrn', value=>$ptrn, size=>20});
#サブミット
print submit('Generate&Refresh').reset('Clear').'   '.'ListViewPassword'.
			input({type=>'password', name=>'lvpass', value=>$lvpass, size=>5}).br,
			end_form.hr;
if($lvpass eq $LVPASSWORD){	#一覧表示用パスワードが入ってないと全部見れない
	if($pass){
		print div('Pass:',$pass).br;
	}
	print $navi, reverse(@data), $navi;	#ナビ、リバースデータ、ナビ
}
print div(a({href=>$REFERER}, 'Password Generator'));
print end_html;
exit;

#重要パスワード作成
sub pwcreate0{
	my $str = shift;								#strに取り出し
	my @sitepiece = split(/\,/,$str);				#分割 0と1
	my $cnt = length($sitepiece[0]);				#文字数カウント
	my $seed = 'p0a0sswor';							#pの基本形	9文字固定　数字は2と4
	my @lcs = $seed =~ /.{1}/g;						#1文字ずつ分割

	my $cntcng = fourSwift($cnt);					#変換
	my @cntlist = $cntcng =~ /.{1}/g;				#分割リスト
	($lcs[1],$lcs[3]) = ($cntlist[0],$cntlist[1]);	#数字変換

	my @fnt = $sitepiece[1] =~ /.{1}/g;				#3分割

	if($cntlist[0]=='3' && $cntlist[1]=='0'){
		$lcs[8]='a';
	}else{
		if($cntlist[0]=='1'){
			$lcs[6]=lc($lcs[6]);					#Lを小文字に
			$lcs[7]=uc($lcs[7]);					#nを大文字に
		}
		$lcs[$cntlist[0]+5] = chr(ord($lcs[$cntlist[0]+5])+$cntlist[1]);	#ずらす

		if($cntlist[0]!='0'){
			$fnt[$cntlist[0]-1] = uc($fnt[$cntlist[0]-1]);	#3文字の1つを大文字に
		}
	}

	my @tempseed = ($lcs[0],$lcs[1],$lcs[2],$lcs[3]);	#一時的に先頭保存
	my $i;
	for($i=0;$i<$cntlist[0];$i++){						#先頭削除
		shift(@lcs);
	}
	for($i=0;$i<3;$i++){								#先頭位置に追加
		unshift(@lcs,$fnt[$i]);
	}
	for($i=$cntlist[0];$i>0;$i--){						#先頭位置に追加
		unshift(@lcs,$tempseed[$i-1]);
	}

	$str = join("",@lcs);								#リスト連結
	return($str);										#返す
}

#頻繁使用パスワード作成
sub pwcreate1{
	my $str = shift;									#strに取り出し
	my @sitepiece = split(/\,/,$str);					#分割 0と1
	my $cnt = length($sitepiece[0]);					#文字数カウント
	my $seed = 'pa00ss';								#bの基本形	6文字固定　数字は3と4
	my @lcs = $seed =~ /.{1}/g;							#1文字ずつ分割

	#my $cntcng = fourSwift($cnt);						#変換
	#my @cntlist = $cntcng =~ /.{1}/g;					#分割リスト
	#($lcs[2],$lcs[3]) = ($cntlist[0],$cntlist[1]);		#数字変換

	my @fnt = $sitepiece[1] =~ /.{1}/g;					#3分割

	unshift(@lcs,$fnt[0]);								#先頭位置に追加
	push(@lcs,$fnt[1]);									#後部位置に追加
	push(@lcs,$fnt[2]);

	$str = join("",@lcs);								#リスト連結
	return($str);										#返す
}

#4進数化&桁入れ替え
sub fourSwift {
	my $str = shift;			#データ引き出し
	my $amr = $str % 4;			#余りゲット
	$str = ($str - $amr) / 4;	#割り切る値
	if($str=='-1'){				#3だけ別枠
		$str = '30';
	}else{
		$str = $amr.$str;		#4進数逆化
	}

	return($str);
}

#保存ファイル作成
sub filecreate{
	# ファイルを作成する。open my $fh, ">", $file

  my $file = shift; # $$ はプロセスID

  if (-e $file) {
    #die "$file は、すでに存在します。";
  }
  else {
    open( my $fh, ">", $file )
      or die "$file を書き込みモードでオープンすることができません。: $!";
    close $fh;
  }
}

